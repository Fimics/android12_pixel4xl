/* GENERATED SOURCE. DO NOT MODIFY. */
package com.android.org.bouncycastle.math.ec;

/**
 * @hide This class is not part of the Android public SDK API
 */
public interface ECLookupTable
{
    int getSize();
    ECPoint lookup(int index);
    ECPoint lookupVar(int index);
}
