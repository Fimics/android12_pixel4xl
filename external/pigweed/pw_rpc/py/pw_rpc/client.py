# Copyright 2020 The Pigweed Authors
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
"""Provides a pw_rpc client for Python."""

import abc
from dataclasses import dataclass
import logging
from typing import (Any, Collection, Dict, Iterable, Iterator, NamedTuple,
                    Optional)

from google.protobuf.message import DecodeError
from pw_status import Status

from pw_rpc import descriptors, packets
from pw_rpc.descriptors import Channel, Service, Method
from pw_rpc.internal.packet_pb2 import PacketType, RpcPacket

_LOG = logging.getLogger(__name__)


class Error(Exception):
    """Error from incorrectly using the RPC client classes."""


class PendingRpc(NamedTuple):
    """Uniquely identifies an RPC call."""
    channel: Channel
    service: Service
    method: Method

    def __str__(self) -> str:
        return f'PendingRpc(channel={self.channel.id}, method={self.method})'


class _PendingRpcMetadata:
    def __init__(self, context: Any, keep_open: bool):
        self.context = context
        self.keep_open = keep_open


class PendingRpcs:
    """Tracks pending RPCs and encodes outgoing RPC packets."""
    def __init__(self):
        self._pending: Dict[PendingRpc, _PendingRpcMetadata] = {}

    def request(self,
                rpc: PendingRpc,
                request,
                context,
                override_pending: bool = True,
                keep_open: bool = False) -> bytes:
        """Starts the provided RPC and returns the encoded packet to send."""
        # Ensure that every context is a unique object by wrapping it in a list.
        self.open(rpc, context, override_pending, keep_open)
        _LOG.debug('Starting %s', rpc)
        return packets.encode_request(rpc, request)

    def send_request(self,
                     rpc: PendingRpc,
                     request,
                     context,
                     override_pending: bool = False,
                     keep_open: bool = False) -> None:
        """Calls request and sends the resulting packet to the channel."""
        # TODO(hepler): Remove `type: ignore` on this and similar lines when
        #     https://github.com/python/mypy/issues/5485 is fixed
        rpc.channel.output(  # type: ignore
            self.request(rpc, request, context, override_pending, keep_open))

    def open(self,
             rpc: PendingRpc,
             context,
             override_pending: bool = False,
             keep_open: bool = False) -> None:
        """Creates a context for an RPC, but does not invoke it.

        open() can be used to receive streaming responses to an RPC that was not
        invoked by this client. For example, a server may stream logs with a
        server streaming RPC prior to any clients invoking it.
        """
        metadata = _PendingRpcMetadata(context, keep_open)

        if override_pending:
            self._pending[rpc] = metadata
        elif self._pending.setdefault(rpc, metadata) is not metadata:
            # If the context was not added, the RPC was already pending.
            raise Error(f'Sent request for {rpc}, but it is already pending! '
                        'Cancel the RPC before invoking it again')

    def cancel(self, rpc: PendingRpc) -> Optional[bytes]:
        """Cancels the RPC. Returns the CANCEL packet to send.

        Returns:
          True if the RPC was cancelled; False if it was not pending

        Raises:
          KeyError if the RPC is not pending
        """
        _LOG.debug('Cancelling %s', rpc)
        del self._pending[rpc]

        if rpc.method.type is Method.Type.UNARY:
            return None

        return packets.encode_cancel(rpc)

    def send_cancel(self, rpc: PendingRpc) -> bool:
        """Calls cancel and sends the cancel packet, if any, to the channel."""
        try:
            packet = self.cancel(rpc)
        except KeyError:
            return False

        if packet:
            rpc.channel.output(packet)  # type: ignore

        return True

    def get_pending(self, rpc: PendingRpc, status: Optional[Status]):
        """Gets the pending RPC's context. If status is set, clears the RPC."""
        if status is None:
            return self._pending[rpc].context

        if self._pending[rpc].keep_open:
            _LOG.debug('%s finished with status %s; keeping open', rpc, status)
            return self._pending[rpc].context

        _LOG.debug('%s finished with status %s', rpc, status)
        return self._pending.pop(rpc).context


class ClientImpl(abc.ABC):
    """The internal interface of the RPC client.

    This interface defines the semantics for invoking an RPC on a particular
    client.
    """
    def __init__(self):
        self.client: 'Client' = None
        self.rpcs: PendingRpcs = None

    @abc.abstractmethod
    def method_client(self, channel: Channel, method: Method) -> Any:
        """Returns an object that invokes a method using the given channel."""

    @abc.abstractmethod
    def handle_response(self,
                        rpc: PendingRpc,
                        context: Any,
                        payload: Any,
                        *,
                        args: tuple = (),
                        kwargs: dict = None) -> Any:
        """Handles a response from the RPC server.

        Args:
          rpc: Information about the pending RPC
          context: Arbitrary context object associated with the pending RPC
          payload: A protobuf message
          args, kwargs: Arbitrary arguments passed to the ClientImpl
        """

    @abc.abstractmethod
    def handle_completion(self,
                          rpc: PendingRpc,
                          context: Any,
                          status: Status,
                          *,
                          args: tuple = (),
                          kwargs: dict = None) -> Any:
        """Handles the successful completion of an RPC.

        Args:
          rpc: Information about the pending RPC
          context: Arbitrary context object associated with the pending RPC
          status: Status returned from the RPC
          args, kwargs: Arbitrary arguments passed to the ClientImpl
        """

    @abc.abstractmethod
    def handle_error(self,
                     rpc: PendingRpc,
                     context,
                     status: Status,
                     *,
                     args: tuple = (),
                     kwargs: dict = None):
        """Handles the abnormal termination of an RPC.

        args:
          rpc: Information about the pending RPC
          context: Arbitrary context object associated with the pending RPC
          status: which error occurred
          args, kwargs: Arbitrary arguments passed to the ClientImpl
        """


class ServiceClient(descriptors.ServiceAccessor):
    """Navigates the methods in a service provided by a ChannelClient."""
    def __init__(self, client_impl: ClientImpl, channel: Channel,
                 service: Service):
        super().__init__(
            {
                method: client_impl.method_client(channel, method)
                for method in service.methods
            },
            as_attrs='members')

        self._channel = channel
        self._service = service

    def __repr__(self) -> str:
        return (f'Service({self._service.full_name!r}, '
                f'methods={[m.name for m in self._service.methods]}, '
                f'channel={self._channel.id})')

    def __str__(self) -> str:
        return str(self._service)


class Services(descriptors.ServiceAccessor[ServiceClient]):
    """Navigates the services provided by a ChannelClient."""
    def __init__(self, client_impl, channel: Channel,
                 services: Collection[Service]):
        super().__init__(
            {s: ServiceClient(client_impl, channel, s)
             for s in services},
            as_attrs='packages')

        self._channel = channel
        self._services = services

    def __repr__(self) -> str:
        return (f'Services(channel={self._channel.id}, '
                f'services={[s.full_name for s in self._services]})')


def _decode_status(rpc: PendingRpc, packet) -> Optional[Status]:
    # Server streaming RPC packets never have a status; all other packets do.
    if packet.type == PacketType.RESPONSE and rpc.method.server_streaming:
        return None

    try:
        return Status(packet.status)
    except ValueError:
        _LOG.warning('Illegal status code %d for %s', packet.status, rpc)

    return None


def _decode_payload(rpc: PendingRpc, packet):
    if packet.type == PacketType.RESPONSE:
        try:
            return packets.decode_payload(packet, rpc.method.response_type)
        except DecodeError as err:
            _LOG.warning('Failed to decode %s response for %s: %s',
                         rpc.method.response_type.DESCRIPTOR.full_name,
                         rpc.method.full_name, err)
    return None


@dataclass(frozen=True, eq=False)
class ChannelClient:
    """RPC services and methods bound to a particular channel.

    RPCs are invoked through service method clients. These may be accessed via
    the `rpcs` member. Service methods use a fully qualified name: package,
    service, method. Service methods may be selected as attributes or by
    indexing the rpcs member by service and method name or ID.

      # Access the service method client as an attribute
      rpc = client.channel(1).rpcs.the.package.FooService.SomeMethod

      # Access the service method client by string name
      rpc = client.channel(1).rpcs[foo_service_id]['SomeMethod']

    RPCs may also be accessed from their canonical name.

      # Access the service method client from its full name:
      rpc = client.channel(1).method('the.package.FooService/SomeMethod')

      # Using a . instead of a / is also supported:
      rpc = client.channel(1).method('the.package.FooService.SomeMethod')

    The ClientImpl class determines the type of the service method client. A
    synchronous RPC client might return a callable object, so an RPC could be
    invoked directly (e.g. rpc(field1=123, field2=b'456')).
    """
    client: 'Client'
    channel: Channel
    rpcs: Services

    def method(self, method_name: str):
        """Returns a method client matching the given name.

        Args:
          method_name: name as package.Service/Method or package.Service.Method.

        Raises:
          ValueError: the method name is not properly formatted
          KeyError: the method is not present
        """
        return descriptors.get_method(self.rpcs, method_name)

    def services(self) -> Iterator:
        return iter(self.rpcs)

    def methods(self) -> Iterator:
        """Iterates over all method clients in this ChannelClient."""
        for service_client in self.rpcs:
            yield from service_client

    def __repr__(self) -> str:
        return (f'ChannelClient(channel={self.channel.id}, '
                f'services={[str(s) for s in self.services()]})')


class Client:
    """Sends requests and handles responses for a set of channels.

    RPC invocations occur through a ChannelClient.
    """
    @classmethod
    def from_modules(cls, impl: ClientImpl, channels: Iterable[Channel],
                     modules: Iterable):
        return cls(
            impl, channels,
            (Service.from_descriptor(service) for module in modules
             for service in module.DESCRIPTOR.services_by_name.values()))

    def __init__(self, impl: ClientImpl, channels: Iterable[Channel],
                 services: Iterable[Service]):
        self._impl = impl
        self._impl.client = self
        self._impl.rpcs = PendingRpcs()

        self.services = descriptors.Services(services)

        self._channels_by_id = {
            channel.id:
            ChannelClient(self, channel,
                          Services(self._impl, channel, self.services))
            for channel in channels
        }

    def channel(self, channel_id: int = None) -> ChannelClient:
        """Returns a ChannelClient, which is used to call RPCs on a channel.

        If no channel is provided, the first channel is used.
        """
        if channel_id is None:
            return next(iter(self._channels_by_id.values()))

        return self._channels_by_id[channel_id]

    def channels(self) -> Iterable[ChannelClient]:
        """Accesses the ChannelClients in this client."""
        return self._channels_by_id.values()

    def method(self, method_name: str) -> Method:
        """Returns a Method matching the given name.

        Args:
          method_name: name as package.Service/Method or package.Service.Method.

        Raises:
          ValueError: the method name is not properly formatted
          KeyError: the method is not present
        """
        return descriptors.get_method(self.services, method_name)

    def methods(self) -> Iterator[Method]:
        """Iterates over all Methods supported by this client."""
        for service in self.services:
            yield from service.methods

    def process_packet(self, pw_rpc_raw_packet_data: bytes, *impl_args,
                       **impl_kwargs) -> Status:
        """Processes an incoming packet.

        Args:
          pw_rpc_raw_packet_data: raw binary data for exactly one RPC packet
          impl_args: optional positional arguments passed to the ClientImpl
          impl_kwargs: optional keyword arguments passed to the ClientImpl

        Returns:
          OK - the packet was processed by this client
          DATA_LOSS - the packet could not be decoded
          INVALID_ARGUMENT - the packet is for a server, not a client
          NOT_FOUND - the packet's channel ID is not known to this client
        """
        try:
            packet = packets.decode(pw_rpc_raw_packet_data)
        except DecodeError as err:
            _LOG.warning('Failed to decode packet: %s', err)
            _LOG.debug('Raw packet: %r', pw_rpc_raw_packet_data)
            return Status.DATA_LOSS

        if packets.for_server(packet):
            return Status.INVALID_ARGUMENT

        try:
            channel_client = self._channels_by_id[packet.channel_id]
        except KeyError:
            _LOG.warning('Unrecognized channel ID %d', packet.channel_id)
            return Status.NOT_FOUND

        try:
            rpc = self._look_up_service_and_method(packet, channel_client)
        except ValueError as err:
            channel_client.channel.output(  # type: ignore
                packets.encode_client_error(packet, Status.NOT_FOUND))
            _LOG.warning('%s', err)
            return Status.OK

        status = _decode_status(rpc, packet)

        if packet.type not in (PacketType.RESPONSE,
                               PacketType.SERVER_STREAM_END,
                               PacketType.SERVER_ERROR):
            _LOG.error('%s: unexpected PacketType %s', rpc, packet.type)
            _LOG.debug('Packet:\n%s', packet)
            return Status.OK

        payload = _decode_payload(rpc, packet)

        try:
            context = self._impl.rpcs.get_pending(rpc, status)
        except KeyError:
            channel_client.channel.output(  # type: ignore
                packets.encode_client_error(packet,
                                            Status.FAILED_PRECONDITION))
            _LOG.debug('Discarding response for %s, which is not pending', rpc)
            return Status.OK

        if packet.type == PacketType.SERVER_ERROR:
            assert status is not None and not status.ok()
            _LOG.warning('%s: invocation failed with %s', rpc, status)
            self._impl.handle_error(rpc,
                                    context,
                                    status,
                                    args=impl_args,
                                    kwargs=impl_kwargs)
            return Status.OK

        if payload is not None:
            self._impl.handle_response(rpc,
                                       context,
                                       payload,
                                       args=impl_args,
                                       kwargs=impl_kwargs)
        if status is not None:
            self._impl.handle_completion(rpc,
                                         context,
                                         status,
                                         args=impl_args,
                                         kwargs=impl_kwargs)

        return Status.OK

    def _look_up_service_and_method(
            self, packet: RpcPacket,
            channel_client: ChannelClient) -> PendingRpc:
        try:
            service = self.services[packet.service_id]
        except KeyError:
            raise ValueError(f'Unrecognized service ID {packet.service_id}')

        try:
            method = service.methods[packet.method_id]
        except KeyError:
            raise ValueError(
                f'No method ID {packet.method_id} in service {service.name}')

        return PendingRpc(channel_client.channel, service, method)

    def __repr__(self) -> str:
        return (f'pw_rpc.Client(channels={list(self._channels_by_id)}, '
                f'services={[s.full_name for s in self.services]})')
