/*
 * Copyright 2020, The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { getPropertiesForDisplay, shortenName } from '../mixin'
import { asRawTreeViewObject } from '../../utils/diff.js'
import { Activity } from "../common"
import WindowContainer from "./WindowContainer"

Activity.fromProto = function (proto): Activity {
    if (proto == null) {
        return null
    } else {
        const children = proto.windowToken.windowContainer.children.reverse()
            .filter(it => it != null)
            .map(it => WindowContainer.childrenFromProto(it, /* isActivityInTree */ true))
        const windowContainer = WindowContainer.fromProto({proto: proto.windowToken.windowContainer,
            children: children, identifierOverride: proto.identifier})
        if (windowContainer == null) {
            throw "Window container should not be null: " + JSON.stringify(proto)
        }
        const entry = new Activity(
            proto.name,
            proto.state,
            proto.visible,
            proto.frontOfTask,
            proto.procId,
            proto.translucent,
            windowContainer
        )

        entry.obj = getPropertiesForDisplay(proto, entry)
        entry.kind = entry.constructor.name
        entry.shortName = shortenName(entry.name)
        entry.rawTreeViewObject = asRawTreeViewObject(entry)

        console.warn("Created ", entry.kind, " stableId=", entry.stableId)
        return entry
    }
}

export default Activity
