/* GENERATED SOURCE. DO NOT MODIFY. */
package com.android.internal.org.bouncycastle.asn1;

import java.io.IOException;

/**
 * Interface implemented by objects that can be converted from streaming to in-memory objects.
 * @hide This class is not part of the Android public SDK API
 */
public interface InMemoryRepresentable
{
    /**
     * Get the in-memory representation of the ASN.1 object.
     * @return an ASN1Primitive representing the loaded object.
     * @throws IOException for bad input data.
     */
    ASN1Primitive getLoadedObject()
        throws IOException;
}
