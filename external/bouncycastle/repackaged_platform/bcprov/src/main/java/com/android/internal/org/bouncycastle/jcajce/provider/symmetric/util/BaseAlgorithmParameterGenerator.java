/* GENERATED SOURCE. DO NOT MODIFY. */
package com.android.internal.org.bouncycastle.jcajce.provider.symmetric.util;

import java.security.AlgorithmParameterGeneratorSpi;
import java.security.AlgorithmParameters;
import java.security.NoSuchAlgorithmException;
import java.security.NoSuchProviderException;
import java.security.SecureRandom;

// Android-changed: Use default provider for JCA algorithms instead of BC
// Was: import org.bouncycastle.jcajce.util.BCJcaJceHelper;
import com.android.internal.org.bouncycastle.jcajce.util.DefaultJcaJceHelper;
import com.android.internal.org.bouncycastle.jcajce.util.JcaJceHelper;

/**
 * @hide This class is not part of the Android public SDK API
 */
public abstract class BaseAlgorithmParameterGenerator
    extends AlgorithmParameterGeneratorSpi
{
    // Android-changed: Use default provider for JCA algorithms instead of BC
    // Was: private final JcaJceHelper helper = new BCJcaJceHelper();
    private final JcaJceHelper helper = new DefaultJcaJceHelper();

    protected SecureRandom  random;
    protected int           strength = 1024;

    public BaseAlgorithmParameterGenerator()
    {
    }

    protected final AlgorithmParameters createParametersInstance(String algorithm)
        throws NoSuchAlgorithmException, NoSuchProviderException
    {
        return helper.createAlgorithmParameters(algorithm);
    }

    protected void engineInit(
        int             strength,
        SecureRandom    random)
    {
        this.strength = strength;
        this.random = random;
    }
}
