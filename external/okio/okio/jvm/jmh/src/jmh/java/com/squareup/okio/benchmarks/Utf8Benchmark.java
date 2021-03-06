/*
 * Copyright (C) 2018 Square, Inc. and others.
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
package com.squareup.okio.benchmarks;

import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;

import org.openjdk.jmh.Main;
import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.Fork;
import org.openjdk.jmh.annotations.Measurement;
import org.openjdk.jmh.annotations.Mode;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Param;
import org.openjdk.jmh.annotations.Scope;
import org.openjdk.jmh.annotations.Setup;
import org.openjdk.jmh.annotations.State;
import org.openjdk.jmh.annotations.Warmup;
import org.openjdk.jmh.runner.RunnerException;

@Fork(1)
@Warmup(iterations = 5, time = 2)
@Measurement(iterations = 5, time = 2)
@State(Scope.Benchmark)
@BenchmarkMode(Mode.Throughput)
@OutputTimeUnit(TimeUnit.SECONDS)
public class Utf8Benchmark {
  private static final Charset utf8 = StandardCharsets.UTF_8;
  private static final Map<String, String> strings = new HashMap<>();

  static {
    strings.put(
        "ascii",
        "Um, I'll tell you the problem with the scientific power that you're using here, "
            + "it didn't require any discipline to attain it. You read what others had done and you "
            + "took the next step. You didn't earn the knowledge for yourselves, so you don't take any "
            + "responsibility for it. You stood on the shoulders of geniuses to accomplish something "
            + "as fast as you could, and before you even knew what you had, you patented it, and "
            + "packaged it, and slapped it on a plastic lunchbox, and now you're selling it, you wanna "
            + "sell it.");

    strings.put(
        "utf8",
        "?????, I'll ????????ll ????????? ????????? ??????????????l??????? ????????????? ???????????? ??????????????????????????????????????? ??????????????????? ?????????????? ????????????'???????? ???????????????? ???????????????, "
            + "???????? ???????????????'???? ??????????????????????????? ???????????? ????????????????????l????????? ???????? ?????????????????????? ????????. ?????????? ??????????????? ??????????????? ???????????????????? ?????????? ?????????????? ???????? ?????????? ?????????????? "
            + "?????????? ??????????????? ??????????????. ??????????? ?????????????'?? ??????????????? ??????????? ?????????????l?????????????? ?????????? ????????????????????????l????????????, ?????? ??????????? ?????????'??? ?????????????? ??????????? "
            + "?????????????????????????????????l???????????? ???????????? ????????. ???????????? ??????????????? ??????? ???????????? ???????????????l??????????????? ???????? ??????????????????????????? ???????? ????????????????????l??????????? ?????????????????????????????????? ???????? ??????????????? "
            + "????? ?????????? ???????????l??, ?????????? ????????????????????? ?????????? ????????????? ????????????? ??????????????? ?????????? ???????????, ??????????? ??????????????????????????????? ??????, ???????????? ????????????????????????? ????????, "
            + "??????????? ????l?????????????????? ?????? ?????? ???? ???l????????????????? l?????????????????????????, ?????????? ?????????? ????????????'???????? ??????ll????????? ??????, ???????????? ?????????????????? ????????ll ????????.");

    // The first 't' is actually a '????'
    strings.put(
        "sparse",
        "Um, I'll ????ell you the problem with the scientific power that you're using here, "
            + "it didn't require any discipline to attain it. You read what others had done and you "
            + "took the next step. You didn't earn the knowledge for yourselves, so you don't take any "
            + "responsibility for it. You stood on the shoulders of geniuses to accomplish something "
            + "as fast as you could, and before you even knew what you had, you patented it, and "
            + "packaged it, and slapped it on a plastic lunchbox, and now you're selling it, you wanna "
            + "sell it.");

    strings.put("2bytes", "\u0080\u07ff");

    strings.put("3bytes", "\u0800\ud7ff\ue000\uffff");

    strings.put("4bytes", "\ud835\udeca");

    // high surrogate, 'a', low surrogate, and 'a'
    strings.put("bad", "\ud800\u0061\udc00\u0061");
  }

  @Param({"20", "2000", "200000"})
  int length;

  @Param({"ascii", "utf8", "sparse", "2bytes", "3bytes", "4bytes", "bad"})
  String encoding;

  String encode;
  byte[] decodeArray;

  @Setup
  public void setup() {
    String part = strings.get(encoding);

    // Make all the strings the same length for comparison
    StringBuilder builder = new StringBuilder(length + 1_000);
    while (builder.length() < length) {
      builder.append(part);
    }
    builder.setLength(length);

    // Prepare a string and byte array for encoding and decoding
    encode = builder.toString();
    decodeArray = encode.getBytes(utf8);
  }

  @Benchmark
  public byte[] stringToBytesOkio() {
    return BenchmarkUtils.encodeUtf8(encode);
  }

  @Benchmark
  public byte[] stringToBytesJava() {
    return encode.getBytes(utf8);
  }

  @Benchmark
  public String bytesToStringOkio() {
    // For ASCII only decoding, this will never be faster than Java. Because
    // Java can trust the decoded char array and it will be the correct size for
    // ASCII, it is able to avoid the extra defensive copy Okio is forced to
    // make because it doesn't have access to String internals.
    return BenchmarkUtils.decodeUtf8(decodeArray);
  }

  @Benchmark
  public String bytesToStringJava() {
    return new String(decodeArray, utf8);
  }

  public static void main(String[] args) throws IOException, RunnerException {
    Main.main(new String[] {Utf8Benchmark.class.getName()});
  }
}
