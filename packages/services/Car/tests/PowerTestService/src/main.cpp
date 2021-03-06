/*
 * Copyright (C) 2018 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#define LOG_TAG "PowerTestService"

#include <signal.h>
#include <utils/Log.h>

#include <binder/IPCThreadState.h>
#include <binder/ProcessState.h>
#include <binder/IServiceManager.h>
#include <binder/IBinder.h>
#include <binder/IInterface.h>

#include "android/car/ICar.h"
#include "android/car/hardware/power/ICarPower.h"
#include "CarPowerManager.h"

using namespace android;
using namespace android::binder;
using namespace android::car;
using namespace android::car::hardware::power;

static std::atomic_bool run(true);

void onStateChanged(CarPowerManager::State state) {
    ALOGI(LOG_TAG "onStateChanged callback = %d", state);
    if (state == CarPowerManager::State::kShutdownPrepare) {
        // Stop the loop
        run = false;
    }
}

int main(int, char**)
{
    int retVal;

    sp<ProcessState> processSelf(ProcessState::self());
    processSelf->startThreadPool();
    ALOGI(LOG_TAG "started");

    std::unique_ptr<CarPowerManager> carPowerManager(new CarPowerManager());

    do {
        retVal = carPowerManager->setListener(onStateChanged);
    } while (retVal != 0);

    do {
        ALOGI(LOG_TAG "Waiting for CarPowerManager listener to initiate SHUTDOWN_PREPARE...");
        sleep(5);
    } while (run);

    ALOGI(LOG_TAG "Exited loop, shutting down");

    // Unregister the listener
    carPowerManager->clearListener();

    // Wait for threads to finish, and then exit.
    IPCThreadState::self()->joinThreadPool();
    return 0;
}

