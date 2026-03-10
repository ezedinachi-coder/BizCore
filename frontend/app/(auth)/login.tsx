import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Image,
  Dimensions,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as WebBrowser from 'expo-web-browser';
import * as Linking from 'expo-linking';
import { Colors, Button } from '../../src/components/ThemedComponents';
import { useAuthStore } from '../../src/store/authStore';

const { width } = Dimensions.get('window');

WebBrowser.maybeCompleteAuthSession();

export default function LoginScreen() {
  const router = useRouter();
  const { login, isAuthenticated } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const hasProcessed = useRef(false);

  // Handle OAuth callback
  useEffect(() => {
    const handleUrl = async (url: string) => {
      if (hasProcessed.current) return;
      
      // Extract session_id from URL fragment
      const hashIndex = url.indexOf('#');
      if (hashIndex !== -1) {
        const fragment = url.substring(hashIndex + 1);
        const params = new URLSearchParams(fragment);
        const sessionId = params.get('session_id');
        
        if (sessionId) {
          hasProcessed.current = true;
          setIsLoading(true);
          try {
            await login(sessionId);
            router.replace('/(tabs)');
          } catch (err: any) {
            setError(err.message || 'Login failed');
            setIsLoading(false);
            hasProcessed.current = false;
          }
        }
      }
    };

    // Check initial URL
    Linking.getInitialURL().then((url) => {
      if (url) handleUrl(url);
    });

    // Listen for URL changes
    const subscription = Linking.addEventListener('url', (event) => {
      handleUrl(event.url);
    });

    return () => subscription.remove();
  }, []);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      router.replace('/(tabs)');
    }
  }, [isAuthenticated]);

  const handleGoogleLogin = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
      const redirectUrl = Linking.createURL('/(auth)/login');
      const authUrl = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
      
      if (Platform.OS === 'web') {
        window.location.href = authUrl;
      } else {
        const result = await WebBrowser.openAuthSessionAsync(authUrl, redirectUrl);
        
        if (result.type === 'success' && result.url) {
          // Extract session_id from the returned URL
          const hashIndex = result.url.indexOf('#');
          if (hashIndex !== -1) {
            const fragment = result.url.substring(hashIndex + 1);
            const params = new URLSearchParams(fragment);
            const sessionId = params.get('session_id');
            
            if (sessionId) {
              await login(sessionId);
              router.replace('/(tabs)');
              return;
            }
          }
        }
        setIsLoading(false);
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        {/* Logo and Brand */}
        <View style={styles.brandContainer}>
          <View style={styles.logoContainer}>
            <Ionicons name="briefcase" size={48} color={Colors.primary} />
          </View>
          <Text style={styles.appName}>BizCore</Text>
          <Text style={styles.tagline}>Business Management Suite</Text>
        </View>

        {/* Features */}
        <View style={styles.featuresContainer}>
          <View style={styles.featureItem}>
            <Ionicons name="cube-outline" size={24} color={Colors.primary} />
            <Text style={styles.featureText}>Inventory Management</Text>
          </View>
          <View style={styles.featureItem}>
            <Ionicons name="people-outline" size={24} color={Colors.secondary} />
            <Text style={styles.featureText}>Suppliers & Distributors</Text>
          </View>
          <View style={styles.featureItem}>
            <Ionicons name="cart-outline" size={24} color={Colors.warning} />
            <Text style={styles.featureText}>Purchase & Sales Orders</Text>
          </View>
          <View style={styles.featureItem}>
            <Ionicons name="stats-chart-outline" size={24} color={Colors.success} />
            <Text style={styles.featureText}>Reports & Analytics</Text>
          </View>
        </View>

        {/* Login Button */}
        <View style={styles.loginContainer}>
          {error && (
            <View style={styles.errorContainer}>
              <Ionicons name="alert-circle" size={20} color={Colors.danger} />
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}
          
          <TouchableOpacity
            style={styles.googleButton}
            onPress={handleGoogleLogin}
            disabled={isLoading}
            activeOpacity={0.8}
          >
            {isLoading ? (
              <ActivityIndicator color={Colors.text} />
            ) : (
              <>
                <View style={styles.googleIconContainer}>
                  <Ionicons name="logo-google" size={20} color="#EA4335" />
                </View>
                <Text style={styles.googleButtonText}>Continue with Google</Text>
              </>
            )}
          </TouchableOpacity>

          <Text style={styles.disclaimer}>
            By continuing, you agree to our Terms of Service and Privacy Policy
          </Text>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    justifyContent: 'space-between',
    paddingVertical: 40,
  },
  brandContainer: {
    alignItems: 'center',
    marginTop: 40,
  },
  logoContainer: {
    width: 100,
    height: 100,
    borderRadius: 24,
    backgroundColor: `${Colors.primary}20`,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  appName: {
    fontSize: 36,
    fontWeight: '800',
    color: Colors.text,
    letterSpacing: 1,
  },
  tagline: {
    fontSize: 16,
    color: Colors.textSecondary,
    marginTop: 8,
  },
  featuresContainer: {
    gap: 16,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.card,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  featureText: {
    fontSize: 16,
    color: Colors.text,
    marginLeft: 12,
  },
  loginContainer: {
    gap: 16,
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: `${Colors.danger}20`,
    padding: 12,
    borderRadius: 8,
  },
  errorText: {
    color: Colors.danger,
    marginLeft: 8,
    flex: 1,
  },
  googleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.card,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  googleIconContainer: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: Colors.text,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  googleButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
  },
  disclaimer: {
    fontSize: 12,
    color: Colors.textMuted,
    textAlign: 'center',
  },
});
