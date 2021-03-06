/* GENERATED SOURCE. DO NOT MODIFY. */
package com.android.org.bouncycastle.asn1;

/**
 *
 * @deprecated Use ASN1ObjectIdentifier instead of this,
 * @hide This class is not part of the Android public SDK API
 */
public class DERObjectIdentifier
    extends ASN1ObjectIdentifier
{
    @android.compat.annotation.UnsupportedAppUsage(maxTargetSdk = 30, trackingBug = 170729553)
    public DERObjectIdentifier(String identifier)
    {
        super(identifier);
    }

    DERObjectIdentifier(byte[] bytes)
    {
        super(bytes);
    }

    DERObjectIdentifier(ASN1ObjectIdentifier oid, String branch)
    {
        super(oid, branch);
    }
}
