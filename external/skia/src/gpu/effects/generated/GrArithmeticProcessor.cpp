/*
 * Copyright 2020 Google Inc.
 *
 * Use of this source code is governed by a BSD-style license that can be
 * found in the LICENSE file.
 */

/**************************************************************************************************
 *** This file was autogenerated from GrArithmeticProcessor.fp; do not modify.
 **************************************************************************************************/
#include "GrArithmeticProcessor.h"

#include "src/core/SkUtils.h"
#include "src/gpu/GrTexture.h"
#include "src/gpu/glsl/GrGLSLFragmentProcessor.h"
#include "src/gpu/glsl/GrGLSLFragmentShaderBuilder.h"
#include "src/gpu/glsl/GrGLSLProgramBuilder.h"
#include "src/sksl/SkSLCPP.h"
#include "src/sksl/SkSLUtil.h"
class GrGLSLArithmeticProcessor : public GrGLSLFragmentProcessor {
public:
    GrGLSLArithmeticProcessor() {}
    void emitCode(EmitArgs& args) override {
        GrGLSLFPFragmentBuilder* fragBuilder = args.fFragBuilder;
        const GrArithmeticProcessor& _outer = args.fFp.cast<GrArithmeticProcessor>();
        (void)_outer;
        auto k = _outer.k;
        (void)k;
        auto enforcePMColor = _outer.enforcePMColor;
        (void)enforcePMColor;
        kVar = args.fUniformHandler->addUniform(
                &_outer, kFragment_GrShaderFlag, kFloat4_GrSLType, "k");
        SkString _sample0 = this->invokeChild(0, args);
        fragBuilder->codeAppendf(
                R"SkSL(half4 src = %s;)SkSL", _sample0.c_str());
        SkString _sample1 = this->invokeChild(1, args);
        fragBuilder->codeAppendf(
                R"SkSL(
half4 dst = %s;
half4 color = clamp((((half(%s.x) * src) * dst + half(%s.y) * src) + half(%s.z) * dst) + half(%s.w), 0.0, 1.0);
@if (%s) {
    color.xyz = min(color.xyz, color.w);
}
return color;
)SkSL",
                _sample1.c_str(),
                args.fUniformHandler->getUniformCStr(kVar),
                args.fUniformHandler->getUniformCStr(kVar),
                args.fUniformHandler->getUniformCStr(kVar),
                args.fUniformHandler->getUniformCStr(kVar),
                (_outer.enforcePMColor ? "true" : "false"));
    }

private:
    void onSetData(const GrGLSLProgramDataManager& pdman,
                   const GrFragmentProcessor& _proc) override {
        const GrArithmeticProcessor& _outer = _proc.cast<GrArithmeticProcessor>();
        { pdman.set4fv(kVar, 1, (_outer.k).ptr()); }
    }
    UniformHandle kVar;
};
std::unique_ptr<GrGLSLFragmentProcessor> GrArithmeticProcessor::onMakeProgramImpl() const {
    return std::make_unique<GrGLSLArithmeticProcessor>();
}
void GrArithmeticProcessor::onGetGLSLProcessorKey(const GrShaderCaps& caps,
                                                  GrProcessorKeyBuilder* b) const {
    b->addBool(enforcePMColor, "enforcePMColor");
}
bool GrArithmeticProcessor::onIsEqual(const GrFragmentProcessor& other) const {
    const GrArithmeticProcessor& that = other.cast<GrArithmeticProcessor>();
    (void)that;
    if (k != that.k) return false;
    if (enforcePMColor != that.enforcePMColor) return false;
    return true;
}
GrArithmeticProcessor::GrArithmeticProcessor(const GrArithmeticProcessor& src)
        : INHERITED(kGrArithmeticProcessor_ClassID, src.optimizationFlags())
        , k(src.k)
        , enforcePMColor(src.enforcePMColor) {
    this->cloneAndRegisterAllChildProcessors(src);
}
std::unique_ptr<GrFragmentProcessor> GrArithmeticProcessor::clone() const {
    return std::make_unique<GrArithmeticProcessor>(*this);
}
#if GR_TEST_UTILS
SkString GrArithmeticProcessor::onDumpInfo() const {
    return SkStringPrintf("(k=float4(%f, %f, %f, %f), enforcePMColor=%s)",
                          k.x,
                          k.y,
                          k.z,
                          k.w,
                          (enforcePMColor ? "true" : "false"));
}
#endif
GR_DEFINE_FRAGMENT_PROCESSOR_TEST(GrArithmeticProcessor);
#if GR_TEST_UTILS
std::unique_ptr<GrFragmentProcessor> GrArithmeticProcessor::TestCreate(GrProcessorTestData* d) {
    SkV4 k;
    k.x = d->fRandom->nextF();
    k.y = d->fRandom->nextF();
    k.z = d->fRandom->nextF();
    k.w = d->fRandom->nextF();
    bool enforcePMColor = d->fRandom->nextBool();
    return GrArithmeticProcessor::Make(GrProcessorUnitTest::MakeChildFP(d),
                                       GrProcessorUnitTest::MakeChildFP(d),
                                       k,
                                       enforcePMColor);
}
#endif
