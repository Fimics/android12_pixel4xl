/*
 * Copyright (C) 2011 The Android Open Source Project
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

#include <string_view>

#include "art_method-inl.h"
#include "check_reference_map_visitor.h"
#include "jni.h"

namespace art {

#define CHECK_REGS_ARE_REFERENCES(...) do { \
  int t[] = {__VA_ARGS__}; \
  int t_size = sizeof(t) / sizeof(*t); \
  CheckReferences( \
      t, t_size, GetDexPc(), GetNativePcOffset(), /* search_for_valid_sack_map= */ false); \
} while (false);

static int gJava_StackWalk_refmap_calls = 0;

class TestReferenceMapVisitor : public CheckReferenceMapVisitor {
 public:
  explicit TestReferenceMapVisitor(Thread* thread) REQUIRES_SHARED(Locks::mutator_lock_)
      : CheckReferenceMapVisitor(thread) {}

  bool VisitFrame() override REQUIRES_SHARED(Locks::mutator_lock_) {
    if (CheckReferenceMapVisitor::VisitFrame()) {
      return true;
    }
    ArtMethod* m = GetMethod();
    std::string_view m_name(m->GetName());

    // Given the method name and the number of times the method has been called,
    // we know the Dex registers with live reference values. Assert that what we
    // find is what is expected.
    if (m_name == "$noinline$f") {
      if (gJava_StackWalk_refmap_calls == 1) {
        CHECK_EQ(1U, GetDexPc());
        CHECK_REGS_ARE_REFERENCES(1);
      } else {
        CHECK_EQ(gJava_StackWalk_refmap_calls, 2);
        CHECK_EQ(5U, GetDexPc());
        CHECK_REGS_ARE_REFERENCES(1);
      }
      found_f_ = true;
    } else if (m_name == "$noinline$g") {
      if (gJava_StackWalk_refmap_calls == 1) {
        CHECK_EQ(0xcU, GetDexPc());
        CHECK_REGS_ARE_REFERENCES(0, 2);  // Note that v1 is not in the minimal root set
      } else {
        CHECK_EQ(gJava_StackWalk_refmap_calls, 2);
        CHECK_EQ(0xcU, GetDexPc());
        CHECK_REGS_ARE_REFERENCES(0, 2);
      }
      found_g_ = true;
    } else if (m_name == "shlemiel") {
      if (gJava_StackWalk_refmap_calls == 1) {
        CHECK_EQ(0x380U, GetDexPc());
        CHECK_REGS_ARE_REFERENCES(2, 4, 5, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 21, 25);
      } else {
        CHECK_EQ(gJava_StackWalk_refmap_calls, 2);
        CHECK_EQ(0x380U, GetDexPc());
        CHECK_REGS_ARE_REFERENCES(2, 4, 5, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 21, 25);
      }
      found_shlemiel_ = true;
    }

    return true;
  }

  ~TestReferenceMapVisitor() {
  }

  bool found_f_ = false;
  bool found_g_ = false;
  bool found_shlemiel_ = false;
};

extern "C" JNIEXPORT jint JNICALL Java_Main_testStackWalk(JNIEnv*, jobject, jint count) {
  ScopedObjectAccess soa(Thread::Current());
  CHECK_EQ(count, 0);
  gJava_StackWalk_refmap_calls++;

  // Visitor
  TestReferenceMapVisitor mapper(soa.Self());
  mapper.WalkStack();
  CHECK(mapper.found_f_);
  CHECK(mapper.found_g_);
  CHECK(mapper.found_shlemiel_);

  return count + 1;
}

}  // namespace art
