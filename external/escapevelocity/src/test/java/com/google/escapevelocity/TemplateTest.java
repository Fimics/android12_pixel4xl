/*
 * Copyright (C) 2018 Google, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.google.escapevelocity;

import static com.google.common.truth.Truth.assertThat;
import static com.google.common.truth.Truth.assertWithMessage;
import static org.junit.Assert.fail;

import com.google.common.collect.ImmutableList;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSetMultimap;
import com.google.common.truth.Expect;
import java.io.ByteArrayInputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.io.StringReader;
import java.io.StringWriter;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.TreeMap;
import java.util.function.Supplier;
import org.apache.commons.collections.ExtendedProperties;
import org.apache.velocity.VelocityContext;
import org.apache.velocity.exception.ResourceNotFoundException;
import org.apache.velocity.exception.VelocityException;
import org.apache.velocity.runtime.RuntimeConstants;
import org.apache.velocity.runtime.RuntimeInstance;
import org.apache.velocity.runtime.log.NullLogChute;
import org.apache.velocity.runtime.parser.node.SimpleNode;
import org.apache.velocity.runtime.resource.Resource;
import org.apache.velocity.runtime.resource.loader.ResourceLoader;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TestName;
import org.junit.runner.RunWith;
import org.junit.runners.JUnit4;

/**
 * @author emcmanus@google.com (??amonn McManus)
 */
@RunWith(JUnit4.class)
public class TemplateTest {
  @Rule public TestName testName = new TestName();
  @Rule public Expect expect = Expect.create();

  private RuntimeInstance velocityRuntimeInstance;

  @Before
  public void initVelocityRuntimeInstance() {
    velocityRuntimeInstance = newVelocityRuntimeInstance();
    velocityRuntimeInstance.init();
  }

  private RuntimeInstance newVelocityRuntimeInstance() {
    RuntimeInstance runtimeInstance = new RuntimeInstance();

    // Ensure that $undefinedvar will produce an exception rather than outputting $undefinedvar.
    runtimeInstance.setProperty(RuntimeConstants.RUNTIME_REFERENCES_STRICT, "true");

    // Disable any logging that Velocity might otherwise see fit to do.
    runtimeInstance.setProperty(RuntimeConstants.RUNTIME_LOG_LOGSYSTEM_CLASS, new NullLogChute());
    runtimeInstance.setProperty(RuntimeConstants.RUNTIME_LOG_LOGSYSTEM, new NullLogChute());
    return runtimeInstance;
  }

  private void compare(String template) {
    compare(template, ImmutableMap.<String, Object>of());
  }

  private void compare(String template, Map<String, ?> vars) {
    compare(template, () -> vars);
  }

  /**
   * Checks that the given template and the given variables produce identical results with
   * Velocity and EscapeVelocity. This uses a {@code Supplier} to define the variables to cover
   * test cases that involve modifying the values of the variables. Otherwise the run using
   * Velocity would change those values so that the run using EscapeVelocity would not be starting
   * from the same point.
   */
  private void compare(String template, Supplier<? extends Map<String, ?>> varsSupplier) {
    Map<String, ?> velocityVars = varsSupplier.get();
    String velocityRendered = velocityRender(template, velocityVars);
    Map<String, ?> escapeVelocityVars = varsSupplier.get();
    String escapeVelocityRendered;
    try {
      escapeVelocityRendered =
          Template.parseFrom(new StringReader(template)).evaluate(escapeVelocityVars);
    } catch (Exception e) {
      throw new AssertionError(
          "EscapeVelocity failed, but Velocity succeeded and returned: <" + velocityRendered + ">",
          e);
    }
    String failure = "from Velocity: <" + velocityRendered + ">\n"
        + "from EscapeVelocity: <" + escapeVelocityRendered + ">\n";
    expect.withMessage(failure).that(escapeVelocityRendered).isEqualTo(velocityRendered);
  }

  private String velocityRender(String template, Map<String, ?> vars) {
    VelocityContext velocityContext = new VelocityContext(new TreeMap<>(vars));
    StringWriter writer = new StringWriter();
    SimpleNode parsedTemplate;
    try {
      parsedTemplate = velocityRuntimeInstance.parse(
          new StringReader(template), testName.getMethodName());
    } catch (org.apache.velocity.runtime.parser.ParseException e) {
      throw new AssertionError(e);
    }
    boolean rendered = velocityRuntimeInstance.render(
        velocityContext, writer, parsedTemplate.getTemplateName(), parsedTemplate);
    assertThat(rendered).isTrue();
    return writer.toString();
  }

  private void expectParseException(
      String template,
      String expectedMessageSubstring) {
    Exception velocityException = null;
    try {
      SimpleNode parsedTemplate =
          velocityRuntimeInstance.parse(new StringReader(template), testName.getMethodName());
      VelocityContext velocityContext = new VelocityContext(new TreeMap<>());
      velocityRuntimeInstance.render(
          velocityContext, new StringWriter(), parsedTemplate.getTemplateName(), parsedTemplate);
      fail("Velocity did not throw an exception for this template");
    } catch (org.apache.velocity.runtime.parser.ParseException | VelocityException expected) {
      velocityException = expected;
    }
    try {
      Template.parseFrom(new StringReader(template));
      fail("Velocity generated an exception, but EscapeVelocity did not: " + velocityException);
    } catch (IOException e) {
      throw new UncheckedIOException(e);
    } catch (ParseException expected) {
      assertWithMessage("Got expected exception, but message did not match")
          .that(expected).hasMessageThat().contains(expectedMessageSubstring);
    }
  }

  @Test
  public void empty() {
    compare("");
  }

  @Test
  public void literalOnly() {
    compare("In the reign of James the Second \n It was generally reckoned\n");
  }

  @Test
  public void lineComment() {
    compare("line 1 ##\n  line 2");
  }

  @Test
  public void blockComment() {
    compare("line 1 #* blah\n line 2 * #\n line 3 *#  \n line 4");
    compare("foo #*# bar *# baz");
    compare("foo #* one *# #* two *# #* three *#");
    compare("foo #** bar *# #* baz **#");
  }

  @Test
  public void ignoreHashIfNotDirectiveOrComment() {
    compare("# if is not a directive because of the space");
    compare("#<foo>");
    compare("# <foo>");
    compare("${foo}#${bar}", ImmutableMap.of("foo", "xxx", "bar", "yyy"));
  }

  @Test
  public void blockQuote() {
    compare("#[[]]#");
    compare("x#[[]]#y");
    compare("#[[$notAReference #notADirective]]#");
    compare("#[[ [[  ]]  ]#  ]]#");
    compare("#[ foo");
    compare("x\n  #[[foo\nbar\nbaz]]#y");
  }

  @Test
  public void substituteNoBraces() {
    compare(" $x ", ImmutableMap.of("x", 1729));
    compare(" ! $x ! ", ImmutableMap.of("x", 1729));
  }

  @Test
  public void dollarWithoutId() {
    compare(" $? ");
    compare(" $$ ");
    compare(" $. ");
    compare(" $[ ");
  }

  @Test
  public void doubleDollar() {
    // The first $ is plain text and the second one starts a reference.
    compare(" $$foo ", ImmutableMap.of("foo", true));
    compare(" $${foo} ", ImmutableMap.of("foo", true));
  }

  @Test
  public void substituteWithBraces() {
    compare("a${x}\nb", ImmutableMap.of("x", "1729"));
  }

  @Test
  public void substitutePropertyNoBraces() {
    compare("=$t.name=", ImmutableMap.of("t", Thread.currentThread()));
  }

  @Test
  public void substitutePropertyWithBraces() {
    compare("=${t.name}=", ImmutableMap.of("t", Thread.currentThread()));
  }

  @Test
  public void substituteNotPropertyId() {
    compare("$foo.!", ImmutableMap.of("foo", false));
  }

  @Test
  public void substituteNestedProperty() {
    compare("\n$t.name.empty\n", ImmutableMap.of("t", Thread.currentThread()));
  }

  @Test
  public void substituteMethodNoArgs() {
    compare("<$c.size()>", ImmutableMap.of("c", ImmutableMap.of()));
  }

  @Test
  public void substituteMethodNoArgsSyntheticOverride() {
    compare("<$c.isEmpty()>", ImmutableMap.of("c", ImmutableSetMultimap.of()));
  }

  @Test
  public void substituteMethodOneArg() {
    compare("<$list.get(0)>", ImmutableMap.of("list", ImmutableList.of("foo")));
  }

  @Test
  public void substituteMethodOneNullArg() {
    // This should evaluate map.containsKey(map.get("absent")), which is map.containsKey(null).
    compare("<$map.containsKey($map.get(\"absent\"))>", ImmutableMap.of("map", ImmutableMap.of()));
  }

  @Test
  public void substituteMethodTwoArgs() {
    compare("\n$s.indexOf(\"bar\", 2)\n", ImmutableMap.of("s", "barbarbar"));
  }

  @Test
  public void substituteMethodSyntheticOverloads() {
    // If we aren't careful, we'll see both the inherited `Set<K> keySet()` from Map
    // and the overridden `ImmutableSet<K> keySet()` in ImmutableMap.
    compare("$map.keySet()", ImmutableMap.of("map", ImmutableMap.of("foo", "bar")));
  }

  @Test
  public void substituteStaticMethod() {
    compare("$Integer.toHexString(23)", ImmutableMap.of("Integer", Integer.class));
  }

  @Test
  public void substituteStaticMethodAsInstanceMethod() {
    compare("$i.toHexString(23)", ImmutableMap.of("i", 0));
  }

  @Test
  public void substituteClassMethod() {
    // This is Class.getName().
    compare("$Integer.getName()", ImmutableMap.of("Integer", Integer.class));
  }

  /** See {@link #substituteClassOrInstanceMethod}. */
  public static class GetName {
    public static String getName() {
      return "Noddy";
    }
  }

  @Test
  public void substituteClassOrInstanceMethod() {
    // If the method exists as both an instance method on Class and a static method on the named
    // class, it's the instance method that wins, so this is still Class.getName().
    compare("$GetName.getName()", ImmutableMap.of("GetName", GetName.class));
  }

  @Test
  public void substituteIndexNoBraces() {
    compare("<$map[\"x\"]>", ImmutableMap.of("map", ImmutableMap.of("x", "y")));
  }

  @Test
  public void substituteIndexWithBraces() {
    compare("<${map[\"x\"]}>", ImmutableMap.of("map", ImmutableMap.of("x", "y")));
  }

  // Velocity allows you to write $map.foo instead of $map["foo"].
  @Test
  public void substituteMapProperty() {
    compare("$map.foo", ImmutableMap.of("map", ImmutableMap.of("foo", "bar")));
    // $map.empty is always equivalent to $map["empty"], never Map.isEmpty().
    compare("$map.empty", ImmutableMap.of("map", ImmutableMap.of("empty", "foo")));
  }

  @Test
  public void substituteIndexThenProperty() {
    compare("<$map[2].name>", ImmutableMap.of("map", ImmutableMap.of(2, getClass())));
  }

  @Test
  public void variableNameCantStartWithNonAscii() {
    compare("<$??amonn>", ImmutableMap.<String, Object>of());
  }

  @Test
  public void variableNamesAreAscii() {
    compare("<$P??draig>", ImmutableMap.of("P", "(P)"));
  }

  @Test
  public void variableNameCharacters() {
    compare("<AZaz-foo_bar23>", ImmutableMap.of("AZaz-foo_bar23", "(P)"));
  }

  /**
   * A public class with a public {@code get} method that has one argument. That means instances can
   * be used like {@code $indexable["foo"]}.
   */
  public static class Indexable {
    public String get(String y) {
      return "[" + y + "]";
    }
  }

  @Test
  public void substituteExoticIndex() {
    // Any class with a get(X) method can be used with $x[i]
    compare("<$x[\"foo\"]>", ImmutableMap.of("x", new Indexable()));
  }

  @Test
  public void substituteInString() {
    String template =
        "#foreach ($a in $list)"
            + "#set ($s = \"THING_${foreach.index}\")"
            + "$s,$s;"
            + "#end";
    compare(template, ImmutableMap.of("list", ImmutableList.of(1, 2, 3)));
    compare("#set ($s = \"$x\") <$s>", ImmutableMap.of("x", "fred"));
    compare("#set ($s = \"==$x$y\") <$s>", ImmutableMap.of("x", "fred", "y", "jim"));
    compare("#set ($s = \"$x$y==\") <$s>", ImmutableMap.of("x", "fred", "y", "jim"));
  }

  @Test
  public void stringOperationsOnSubstitution() {
    compare("#set ($s = \"a${b}c\") $s.length()", ImmutableMap.of("b", 23));
  }

  @Test
  public void singleQuoteNoSubstitution() {
    compare("#set ($s = 'a${b}c') x${s}y", ImmutableMap.of("b", 23));
  }

  @Test
  public void simpleSet() {
    compare("$x#set ($x = 17)#set ($y = 23) ($x, $y)", ImmutableMap.of("x", 1));
  }

  @Test
  public void newlineAfterSet() {
    compare("foo #set ($x = 17)\nbar", ImmutableMap.<String, Object>of());
  }

  @Test
  public void newlineInSet() {
    compare("foo #set ($x\n  = 17)\nbar $x", ImmutableMap.<String, Object>of());
  }

  @Test
  public void expressions() {
    compare("#set ($x = 1 + 1) $x");
    compare("#set ($x = 1 + 2 * 3) $x");
    compare("#set ($x = (1 + 1 == 2)) $x");
    compare("#set ($x = (1 + 1 != 2)) $x");
    compare("#set ($x = 22 - 7) $x");
    compare("#set ($x = 22 / 7) $x");
    compare("#set ($x = 22 % 7) $x");
  }

  @Test
  public void associativity() {
    compare("#set ($x = 3 - 2 - 1) $x");
    compare("#set ($x = 16 / 4 / 4) $x");
  }

  @Test
  public void precedence() {
    compare("#set ($x = 1 + 2 + 3 * 4 * 5 + 6) $x");
    compare("#set($x=1+2+3*4*5+6)$x");
    compare("#set ($x = 1 + 2 * 3 == 3 * 2 + 1) $x");
  }

  @Test
  public void and() {
    compare("#set ($x = false && false) $x");
    compare("#set ($x = false && true) $x");
    compare("#set ($x = true && false) $x");
    compare("#set ($x = true && true) $x");
  }

  @Test
  public void or() {
    compare("#set ($x = false || false) $x");
    compare("#set ($x = false || true) $x");
    compare("#set ($x = true || false) $x");
    compare("#set ($x = true || true) $x");
  }

  @Test
  public void not() {
    compare("#set ($x = !true) $x");
    compare("#set ($x = !false) $x");
  }

  @Test
  public void truthValues() {
    compare("#set ($x = $true && true) $x", ImmutableMap.of("true", true));
    compare("#set ($x = $false && true) $x", ImmutableMap.of("false", false));
    compare("#set ($x = $emptyCollection && true) $x",
        ImmutableMap.of("emptyCollection", ImmutableList.of()));
    compare("#set ($x = $emptyString && true) $x", ImmutableMap.of("emptyString", ""));
  }

  @Test
  public void numbers() {
    compare("#set ($x = 0) $x");
    compare("#set ($x = -1) $x");
    compare("#set ($x = " + Integer.MAX_VALUE + ") $x");
    compare("#set ($x = " + Integer.MIN_VALUE + ") $x");
  }

  private static final String[] RELATIONS = {"==", "!=", "<", ">", "<=", ">="};

  @Test
  public void intRelations() {
    int[] numbers = {-1, 0, 1, 17};
    for (String relation : RELATIONS) {
      for (int a : numbers) {
        for (int b : numbers) {
          compare("#set ($x = $a " + relation + " $b) $x",
              ImmutableMap.<String, Object>of("a", a, "b", b));
        }
      }
    }
  }

  @Test
  public void relationPrecedence() {
    compare("#set ($x = 1 < 2 == 2 < 1) $x");
    compare("#set ($x = 2 < 1 == 2 < 1) $x");
  }

  /**
   * Tests the surprising definition of equality mentioned in
   * {@link ExpressionNode.BinaryExpressionNode}.
   */
  @Test
  public void funkyEquals() {
    compare("#set ($t = (123 == \"123\")) $t");
    compare("#set ($f = (123 == \"1234\")) $f");
    compare("#set ($x = ($sb1 == $sb2)) $x", ImmutableMap.of(
        "sb1", (Object) new StringBuilder("123"),
        "sb2", (Object) new StringBuilder("123")));
  }

  @Test
  public void ifTrueNoElse() {
    compare("x#if (true)y #end z");
    compare("x#if (true)y #end  z");
    compare("x#if (true)y #end\nz");
    compare("x#if (true)y #end\n z");
    compare("x#if (true) y #end\nz");
    compare("x#if (true)\ny #end\nz");
    compare("x#if (true) y #end\nz");
    compare("$x #if (true) y #end $x ", ImmutableMap.of("x", "!"));
  }

  @Test
  public void ifFalseNoElse() {
    compare("x#if (false)y #end z");
    compare("x#if (false)y #end\nz");
    compare("x#if (false)y #end\n z");
    compare("x#if (false) y #end\nz");
    compare("x#if (false)\ny #end\nz");
    compare("x#if (false) y #end\nz");
  }

  @Test
  public void ifTrueWithElse() {
    compare("x#if (true) a #else b #end z");
  }

  @Test
  public void ifFalseWithElse() {
    compare("x#if (false) a #else b #end z");
  }

  @Test
  public void ifTrueWithElseIf() {
    compare("x#if (true) a #elseif (true) b #else c #end z");
  }

  @Test
  public void ifFalseWithElseIfTrue() {
    compare("x#if (false) a #elseif (true) b #else c #end z");
  }

  @Test
  public void ifFalseWithElseIfFalse() {
    compare("x#if (false) a #elseif (false) b #else c #end z");
  }

  @Test
  public void ifBraces() {
    compare("x#{if}(false)a#{elseif}(false)b #{else}c#{end}z");
  }
  @Test
  public void ifUndefined() {
    compare("#if ($undefined) really? #else indeed #end");
  }

  @Test
  public void forEach() {
    compare("x#foreach ($x in $c) <$x> #end y",
        ImmutableMap.of("c", ImmutableList.of()));
    compare("x#foreach ($x in $c) <$x> #end y",
        ImmutableMap.of("c", ImmutableList.of("foo", "bar", "baz")));
    compare("x#foreach ($x in $c) <$x> #end y",
        ImmutableMap.of("c", new String[] {"foo", "bar", "baz"}));
    compare("x#foreach ($x in $c) <$x> #end y",
        ImmutableMap.of("c", ImmutableMap.of("foo", "bar", "baz", "buh")));
  }

  @Test
  public void forEachHasNext() {
    compare("x#foreach ($x in $c) <$x#if ($foreach.hasNext), #end> #end y",
        ImmutableMap.of("c", ImmutableList.of()));
    compare("x#foreach ($x in $c) <$x#if ($foreach.hasNext), #end> #end y",
        ImmutableMap.of("c", ImmutableList.of("foo", "bar", "baz")));
  }

  @Test
  public void nestedForEach() {
    String template =
        "$x #foreach ($x in $listOfLists)\n"
        + "  #foreach ($y in $x)\n"
        + "    ($y)#if ($foreach.hasNext), #end\n"
        + "  #end#if ($foreach.hasNext); #end\n"
        + "#end\n"
        + "$x\n";
    Object listOfLists = ImmutableList.of(
        ImmutableList.of("foo", "bar", "baz"), ImmutableList.of("fred", "jim", "sheila"));
    compare(template, ImmutableMap.of("x", 23, "listOfLists", listOfLists));
  }

  @Test
  public void forEachScope() {
    String template =
        "$x #foreach ($x in $list)\n"
        + "[$x]\n"
        + "#set ($x = \"bar\")\n"
        + "#set ($othervar = \"baz\")\n"
        + "#end\n"
        + "$x $othervar";
    compare(
        template, ImmutableMap.of("x", "foo", "list", ImmutableList.of("blim", "blam", "blum")));
  }

  @Test
  public void forEachIndex() {
    String template =
        "#foreach ($x in $list)"
            + "[$foreach.index]"
            + "#foreach ($y in $list)"
            + "($foreach.index)==$x.$y=="
            + "#end"
            + "#end";
    compare(template, ImmutableMap.of("list", ImmutableList.of("blim", "blam", "blum")));
  }

  @Test
  public void setSpacing() {
    // The spacing in the output from #set is eccentric.
    compare("x#set ($x = 0)x");
    compare("x #set ($x = 0)x");
    compare("x #set ($x = 0) x");
    compare("$x#set ($x = 0)x", ImmutableMap.of("x", "!"));

    // Velocity WTF: the #set eats the space after $x and other references, so the output is <!x>.
    compare("$x  #set ($x = 0)x", ImmutableMap.of("x", "!"));
    compare("$x.length()  #set ($x = 0)x", ImmutableMap.of("x", "!"));
    compare("$x.empty  #set ($x = 0)x", ImmutableMap.of("x", "!"));
    compare("$x[0]  #set ($x = 0)x", ImmutableMap.of("x", ImmutableList.of("!")));

    compare("x#set ($x = 0)\n  $x!");

    compare("x  #set($x = 0)  #set($x = 0)  #set($x = 0)  y");

    compare("x ## comment\n  #set($x = 0)  y");
    compare("x #* comment *#    #set($x = 0)  y");
  }

  @Test
  public void simpleMacro() {
    String template =
        "xyz\n"
        + "#macro (m)\n"
        + "hello world\n"
        + "#end\n"
        + "#m() abc #m()\n";
    compare(template);
  }

  @Test
  public void macroWithArgs() {
    String template =
        "$x\n"
        + "#macro (m $x $y)\n"
        + "  #if ($x < $y) less #else greater #end\n"
        + "#end\n"
        + "#m(17 23) #m(23 17) #m(17 17)\n"
        + "$x";
    compare(template, ImmutableMap.of("x", "tiddly"));
  }

  @Test
  public void macroWithCommaSeparatedArgs() {
    String template =
        "$x\n"
        + "#macro (m, $x, $y)\n"
        + "  #if ($x < $y) less #else greater #end\n"
        + "#end\n"
        + "#m(17 23) #m(23 17) #m(17 17)\n"
        + "$x";
    compare(template, ImmutableMap.of("x", "tiddly"));
  }

  /**
   * Tests defining a macro inside a conditional. This proves that macros are not evaluated in the
   * main control flow, but rather are extracted at parse time. It also tests what happens if there
   * is more than one definition of the same macro. (It is not apparent from the test, but it is the
   * first definition that is retained.)
   */
  @Test
  public void conditionalMacroDefinition() {
    String templateFalse =
        "#if (false)\n"
        + "  #macro (m) foo #end\n"
        + "#else\n"
        + "  #macro (m) bar #end\n"
        + "#end\n"
        + "#m()\n";
    compare(templateFalse);

    String templateTrue =
        "#if (true)\n"
        + "  #macro (m) foo #end\n"
        + "#else\n"
        + "  #macro (m) bar #end\n"
        + "#end\n"
        + "#m()\n";
    compare(templateTrue);
  }

  /**
   * Tests referencing a macro before it is defined. Since macros are extracted at parse time but
   * references are only used at evaluation time, this works.
   */
  @Test
  public void forwardMacroReference() {
    String template =
        "#m(17)\n"
        + "#macro (m $x)\n"
        + "  !$x!\n"
        + "#end";
    compare(template);
  }

  @Test
  public void macroArgsSeparatedBySpaces() {
    String template =
        "#macro (sum $x $y $z)\n"
        + "  #set ($sum = $x + $y + $z)\n"
        + "  $sum\n"
        + "#end\n"
        + "#sum ($list[0] $list.get(1) 5)\n";
    compare(template, ImmutableMap.of("list", ImmutableList.of(3, 4)));
  }

  @Test
  public void macroArgsSeparatedByCommas() {
    String template =
        "#macro (sum $x $y $z)\n"
        + "  #set ($sum = $x + $y + $z)\n"
        + "  $sum\n"
        + "#end\n"
        + "#sum ($list[0],$list.get(1),5)\n";
    compare(template, ImmutableMap.of("list", ImmutableList.of(3, 4)));
  }

  // The following tests are based on http://wiki.apache.org/velocity/MacroEvaluationStrategy.
  // They verify some of the trickier details of Velocity's call-by-name semantics.

  @Test
  public void callBySharing() {
    // The example on the web page is wrong because $map.put('x', 'a') evaluates to null, which
    // Velocity rejects as a render error. We fix this by ensuring that the returned previous value
    // is not null.
    // Here, the value of $y should not be affected by #set($x = "a"), even though the name passed
    // to $x is $y.
    String template =
        "#macro(callBySharing $x $map)\n"
        + "  #set($x = \"a\")\n"
        + "  $map.put(\"x\", \"a\")\n"
        + "#end\n"
        + "#callBySharing($y $map)\n"
        + "y is $y\n"
        + "map[x] is $map[\"x\"]\n";
    Supplier<Map<String, Object>> makeMap = new Supplier<Map<String, Object>>() {
      @Override public Map<String, Object> get() {
        return ImmutableMap.<String, Object>of(
            "y", "y",
            "map", new HashMap<String, Object>(ImmutableMap.of("x", (Object) "foo")));
      }
    };
    compare(template, makeMap);
  }

  @Test
  public void callByMacro() {
    // Since #callByMacro1 never references its argument, $x.add("t") is never evaluated during it.
    // Since #callByMacro2 references its argument twice, $x.add("t") is evaluated twice during it.
    String template =
        "#macro(callByMacro1 $p)\n"
        + "  not using\n"
        + "#end\n"
        + "#macro(callByMacro2 $p)\n"
        + "  using: $p\n"
        + "  using again: $p\n"
        + "  using again: $p\n"
        + "#end\n"
        + "#callByMacro1($x.add(\"t\"))\n"
        + "x = $x\n"
        + "#callByMacro2($x.add(\"t\"))\n"
        + "x = $x\n";
    Supplier<Map<String, Object>> makeMap = new Supplier<Map<String, Object>>() {
      @Override public Map<String, Object> get() {
        return ImmutableMap.<String, Object>of("x", new ArrayList<Object>());
      }
    };
    compare(template, makeMap);
  }

  @Test
  public void callByValue() {
    // The assignments to the macro parameters $a and $b cause those parameters to be shadowed,
    // so the output is: a b becomes b a.
    String template =
        "#macro(callByValueSwap $a $b)\n"
        + "  $a $b becomes\n"
        + "  #set($tmp = $a)\n"
        + "  #set($a = $b)\n"
        + "  #set($b = $tmp)\n"
        + "  $a $b\n"
        + "#end"
        + "#callByValueSwap(\"a\", \"b\")";
    compare(template);
  }

  // First "Call by macro expansion example" doesn't apply as long as we don't have map literals.

  @Test
  public void nameCaptureSwap() {
    // Here, the arguments $a and $b are variables rather than literals, which means that their
    // values change when we set those variables. #set($tmp = $a) changes the meaning of $b since
    // $b is the name $tmp. So #set($a = $b) shadows parameter $a with the value of $tmp, which we
    // have just set to "a". Then #set($b = $tmp) shadows parameter $b also with the value of $tmp.
    // The end result is: a b becomes a a.
    String template =
        "#macro(nameCaptureSwap $a $b)\n"
        + "  $a $b becomes\n"
        + "  #set($tmp = $a)\n"
        + "  #set($a = $b)\n"
        + "  #set($b = $tmp)\n"
        + "  $a $b\n"
        + "#end\n"
        + "#set($x = \"a\")\n"
        + "#set($tmp = \"b\")\n"
        + "#nameCaptureSwap($x $tmp)";
    compare(template);
  }

  @Test
  public void badBraceReference() {
    String template = "line 1\nline 2\nbar${foo.!}baz";
    expectParseException(template, "Expected }, on line 3, at text starting: .!}baz");
  }

  @Test
  public void undefinedMacro() {
    String template = "#oops()";
    expectParseException(
        template,
        "#oops is neither a standard directive nor a macro that has been defined");
  }

  @Test
  public void macroArgumentMismatch() {
    String template =
        "#macro (twoArgs $a $b) $a $b #end\n"
        + "#twoArgs(23)\n";
    expectParseException(template, "Wrong number of arguments to #twoArgs: expected 2, got 1");
  }

  @Test
  public void unclosedBlockQuote() {
    String template = "foo\nbar #[[\nblah\nblah";
    expectParseException(template, "Unterminated #[[ - did not see matching ]]#, on line 2");
  }

  @Test
  public void unclosedBlockComment() {
    compare("foo\nbar #*\nblah\nblah");
  }

  /**
   * A Velocity ResourceLoader that looks resources up in a map. This allows us to test directives
   * that read "resources", for example {@code #parse}, without needing to make separate files to
   * put them in.
   */
  private static final class MapResourceLoader extends ResourceLoader {
    private final ImmutableMap<String, String> resourceMap;

    MapResourceLoader(ImmutableMap<String, String> resourceMap) {
      this.resourceMap = resourceMap;
    }

    @Override
    public void init(ExtendedProperties configuration) {
    }

    @Override
    public InputStream getResourceStream(String source) {
      String resource = resourceMap.get(source);
      if (resource == null) {
        throw new ResourceNotFoundException(source);
      }
      return new ByteArrayInputStream(resource.getBytes(StandardCharsets.ISO_8859_1));
    }

    @Override
    public boolean isSourceModified(Resource resource) {
      return false;
    }

    @Override
    public long getLastModified(Resource resource) {
      return 0;
    }
  };

  private String renderWithResources(
      String templateResourceName,
      ImmutableMap<String, String> resourceMap,
      ImmutableMap<String, String> vars) {
    MapResourceLoader mapResourceLoader = new MapResourceLoader(resourceMap);
    RuntimeInstance runtimeInstance = newVelocityRuntimeInstance();
    runtimeInstance.setProperty("resource.loader", "map");
    runtimeInstance.setProperty("map.resource.loader.instance", mapResourceLoader);
    runtimeInstance.init();
    org.apache.velocity.Template velocityTemplate =
        runtimeInstance.getTemplate(templateResourceName);
    StringWriter velocityWriter = new StringWriter();
    VelocityContext velocityContext = new VelocityContext(new TreeMap<>(vars));
    velocityTemplate.merge(velocityContext, velocityWriter);
    return velocityWriter.toString();
  }

  @Test
  public void parseDirective() throws IOException {
    // If outer.vm does #parse("nested.vm"), then we should be able to #set a variable in
    // nested.vm and use it in outer.vm, and we should be able to define a #macro in nested.vm
    // and call it in outer.vm.
    ImmutableMap<String, String> resources = ImmutableMap.of(
        "outer.vm",
        "first line\n"
            + "#parse (\"nested.vm\")\n"
            + "<#decorate (\"left\" \"right\")>\n"
            + "$baz skidoo\n"
            + "last line\n",
        "nested.vm",
        "nested template first line\n"
            + "[#if ($foo == $bar) equal #else not equal #end]\n"
            + "#macro (decorate $a $b) < $a | $b > #end\n"
            + "#set ($baz = 23)\n"
            + "nested template last line\n");

    ImmutableMap<String, String> vars = ImmutableMap.of("foo", "foovalue", "bar", "barvalue");

    String velocityResult = renderWithResources("outer.vm", resources, vars);

    Template.ResourceOpener resourceOpener = resourceName -> {
      String resource = resources.get(resourceName);
      if (resource == null) {
        throw new FileNotFoundException(resourceName);
      }
      return new StringReader(resource);
    };
    Template template = Template.parseFrom("outer.vm", resourceOpener);

    String result = template.evaluate(vars);
    assertThat(result).isEqualTo(velocityResult);

    ImmutableMap<String, String> badVars = ImmutableMap.of("foo", "foovalue");
    try {
      template.evaluate(badVars);
      fail();
    } catch (EvaluationException e) {
      assertThat(e).hasMessageThat().isEqualTo(
          "In expression on line 2 of nested.vm: Undefined reference $bar");
    }
  }
}
