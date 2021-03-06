// Copyright 2021 The Pigweed Authors
//
// Licensed under the Apache License, Version 2.0 (the "License"); you may not
// use this file except in compliance with the License. You may obtain a copy of
// the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations under
// the License.

#include "pw_sync/binary_semaphore.h"

#include <algorithm>

#include "RTOS.h"
#include "pw_assert/assert.h"
#include "pw_chrono/system_clock.h"
#include "pw_chrono_embos/system_clock_constants.h"
#include "pw_interrupt/context.h"

using pw::chrono::SystemClock;

namespace pw::sync {

bool BinarySemaphore::try_acquire_for(SystemClock::duration for_at_least) {
  PW_DCHECK(!interrupt::InInterruptContext());

  // Use non-blocking try_acquire for negative and zero length durations.
  if (for_at_least <= SystemClock::duration::zero()) {
    return try_acquire();
  }

  // On a tick based kernel we cannot tell how far along we are on the current
  // tick, ergo we add one whole tick to the final duration.
  constexpr SystemClock::duration kMaxTimeoutMinusOne =
      pw::chrono::embos::kMaxTimeout - SystemClock::duration(1);
  while (for_at_least > kMaxTimeoutMinusOne) {
    if (OS_WaitCSemaTimed(&native_type_,
                          static_cast<OS_TIME>(kMaxTimeoutMinusOne.count()))) {
      return true;
    }
    for_at_least -= kMaxTimeoutMinusOne;
  }
  return OS_WaitCSemaTimed(&native_type_,
                           static_cast<OS_TIME>(for_at_least.count() + 1));
}

}  // namespace pw::sync
