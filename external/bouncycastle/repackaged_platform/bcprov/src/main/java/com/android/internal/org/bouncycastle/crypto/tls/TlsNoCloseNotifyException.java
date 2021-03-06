/* GENERATED SOURCE. DO NOT MODIFY. */
package com.android.internal.org.bouncycastle.crypto.tls;

import java.io.EOFException;

/**
 * This exception will be thrown (only) when the connection is closed by the peer without sending a
 * {@link AlertDescription#close_notify close_notify} warning alert. If this happens, the TLS
 * protocol cannot rule out truncation of the connection data (potentially malicious). It may be
 * possible to check for truncation via some property of a higher level protocol built upon TLS,
 * e.g. the Content-Length header for HTTPS.
 *
 * @deprecated Migrate to the (D)TLS API in org.bouncycastle.tls (bctls jar).
 * @hide This class is not part of the Android public SDK API
 */
public class TlsNoCloseNotifyException
    extends EOFException
{
    public TlsNoCloseNotifyException()
    {
        super("No close_notify alert received before connection closed");
    }
}
