// BEGIN-INTERNAL
package org.robolectric.shadows;

import static android.os.Build.VERSION_CODES.Q;
import static android.os.Build.VERSION_CODES.R;
import static java.nio.charset.StandardCharsets.UTF_8;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import org.robolectric.annotation.Implementation;
import org.robolectric.annotation.Implements;
import org.robolectric.util.ReflectionHelpers;
import org.robolectric.util.ReflectionHelpers.ClassParameter;

/** Shadow for TimeZoneFinder on Q,R. */
@Implements(
    className = "libcore.timezone.TimeZoneFinder",
    minSdk = Q,
    maxSdk = R,
    isInAndroidSdk = false,
    looseSignatures = true)
public class ShadowTimeZoneFinderQ {

  private static final String TZLOOKUP_PATH = "/usr/share/zoneinfo/tzlookup.xml";

    @Implementation
    protected static Object getInstance() {
      try {
        return ReflectionHelpers.callStaticMethod(
            Class.forName("libcore.timezone.TimeZoneFinder"),
            "createInstanceForTests",
            ClassParameter.from(String.class, readTzlookup()));
      } catch (ClassNotFoundException e) {
        throw new RuntimeException(e);
      }
    }

  /**
   * Reads tzlookup.xml from the files bundled inside android-all JARs. We need to read the file
   * instead of passing in the path because the real implementation uses {@link java.nio.file.Paths}
   * which doesn't support reading from JARs.
   */
  private static String readTzlookup() {
    StringBuilder stringBuilder = new StringBuilder();
    InputStream is = null;
    try {
      try {
        is = ShadowTimeZoneFinder.class.getResourceAsStream(TZLOOKUP_PATH);
        BufferedReader reader = new BufferedReader(new InputStreamReader(is, UTF_8));
        for (String line; (line = reader.readLine()) != null; ) {
          stringBuilder.append(line);
        }
      } finally {
        if (is != null) {
          is.close();
        }
      }
    } catch (IOException e) {
      // ignore
    }

    return stringBuilder.toString();
  }
}
// END-INTERNAL
