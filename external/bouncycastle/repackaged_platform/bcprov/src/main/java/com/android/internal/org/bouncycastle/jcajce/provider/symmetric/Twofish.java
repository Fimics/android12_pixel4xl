/* GENERATED SOURCE. DO NOT MODIFY. */
package com.android.internal.org.bouncycastle.jcajce.provider.symmetric;

// Android-removed: Unsupported algorithms
// import org.bouncycastle.crypto.BlockCipher;
// import org.bouncycastle.crypto.CipherKeyGenerator;
import com.android.internal.org.bouncycastle.crypto.engines.TwofishEngine;
// Android-removed: Unsupported algorithms
// import org.bouncycastle.crypto.generators.Poly1305KeyGenerator;
// import org.bouncycastle.crypto.macs.GMac;
import com.android.internal.org.bouncycastle.crypto.modes.CBCBlockCipher;
// Android-removed: Unsupported algorithms
// import org.bouncycastle.crypto.modes.GCMBlockCipher;
import com.android.internal.org.bouncycastle.jcajce.provider.config.ConfigurableProvider;
import com.android.internal.org.bouncycastle.jcajce.provider.symmetric.util.BaseBlockCipher;
// Android-removed: Unsupported algorithms
// import org.bouncycastle.jcajce.provider.symmetric.util.BaseKeyGenerator;
// import org.bouncycastle.jcajce.provider.symmetric.util.BaseMac;
// import org.bouncycastle.jcajce.provider.symmetric.util.BlockCipherProvider;
// import org.bouncycastle.jcajce.provider.symmetric.util.IvAlgorithmParameters;
import com.android.internal.org.bouncycastle.jcajce.provider.symmetric.util.PBESecretKeyFactory;

/**
 * @hide This class is not part of the Android public SDK API
 */
public final class Twofish
{
    private Twofish()
    {
    }

    // BEGIN Android-removed: Unsupported algorithms
    /*
    public static class ECB
        extends BaseBlockCipher
    {
        public ECB()
        {
            super(new BlockCipherProvider()
            {
                public BlockCipher get()
                {
                    return new TwofishEngine();
                }
            });
        }
    }

    public static class KeyGen
        extends BaseKeyGenerator
    {
        public KeyGen()
        {
            super("Twofish", 256, new CipherKeyGenerator());
        }
    }

    public static class GMAC
        extends BaseMac
    {
        public GMAC()
        {
            super(new GMac(new GCMBlockCipher(new TwofishEngine())));
        }
    }

    public static class Poly1305
        extends BaseMac
    {
        public Poly1305()
        {
            super(new org.bouncycastle.crypto.macs.Poly1305(new TwofishEngine()));
        }
    }

    public static class Poly1305KeyGen
        extends BaseKeyGenerator
    {
        public Poly1305KeyGen()
        {
            super("Poly1305-Twofish", 256, new Poly1305KeyGenerator());
        }
    }
    */
    // END Android-removed: Unsupported algorithms

    /**
     * PBEWithSHAAndTwofish-CBC
     * @hide This class is not part of the Android public SDK API
     */
    static public class PBEWithSHAKeyFactory
        extends PBESecretKeyFactory
    {
        public PBEWithSHAKeyFactory()
        {
            super("PBEwithSHAandTwofish-CBC", null, true, PKCS12, SHA1, 256, 128);
        }
    }

    /**
     * PBEWithSHAAndTwofish-CBC
     * @hide This class is not part of the Android public SDK API
     */
    static public class PBEWithSHA
        extends BaseBlockCipher
    {
        public PBEWithSHA()
        {
            super(new CBCBlockCipher(new TwofishEngine()), PKCS12, SHA1, 256, 16);
        }
    }

    // BEGIN Android-removed: Unsupported algorithms
    /*
    public static class AlgParams
        extends IvAlgorithmParameters
    {
        protected String engineToString()
        {
            return "Twofish IV";
        }
    }
    */
    // END Android-removed: Unsupported algorithms

    /**
     * @hide This class is not part of the Android public SDK API
     */
    public static class Mappings
        extends SymmetricAlgorithmProvider
    {
        private static final String PREFIX = Twofish.class.getName();

        public Mappings()
        {
        }

        public void configure(ConfigurableProvider provider)
        {
            // BEGIN Android-removed: Unsupported algorithms
            // provider.addAlgorithm("Cipher.Twofish", PREFIX + "$ECB");
            // provider.addAlgorithm("KeyGenerator.Twofish", PREFIX + "$KeyGen");
            // provider.addAlgorithm("AlgorithmParameters.Twofish", PREFIX + "$AlgParams");
            // END Android-removed: Unsupported algorithms

            // Android-note: These algorithms are necessary for KeyStore.BouncyCastle
            provider.addAlgorithm("Alg.Alias.AlgorithmParameters.PBEWITHSHAANDTWOFISH", "PKCS12PBE");
            provider.addAlgorithm("Alg.Alias.AlgorithmParameters.PBEWITHSHAANDTWOFISH-CBC", "PKCS12PBE");
            provider.addAlgorithm("Cipher.PBEWITHSHAANDTWOFISH-CBC",  PREFIX + "$PBEWithSHA");
            provider.addAlgorithm("SecretKeyFactory.PBEWITHSHAANDTWOFISH-CBC", PREFIX + "$PBEWithSHAKeyFactory");

            // BEGIN Android-removed: Unsupported algorithms
            // addGMacAlgorithm(provider, "Twofish", PREFIX + "$GMAC", PREFIX + "$KeyGen");
            // addPoly1305Algorithm(provider, "Twofish", PREFIX + "$Poly1305", PREFIX + "$Poly1305KeyGen");
            // END Android-removed: Unsupported algorithms
        }
    }
}
