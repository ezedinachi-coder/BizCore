import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../utils/api';
import { User } from '../types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  checkAuth: () => Promise<void>;
  login: (sessionId: string) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: User | null) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  checkAuth: async () => {
    try {
      set({ isLoading: true });
      const token = await AsyncStorage.getItem('session_token');
      
      if (!token) {
        set({ user: null, isAuthenticated: false, isLoading: false });
        return;
      }

      const response = await api.get('/auth/me');
      const user = response.data;
      
      await AsyncStorage.setItem('user', JSON.stringify(user));
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error) {
      await AsyncStorage.removeItem('session_token');
      await AsyncStorage.removeItem('user');
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  login: async (sessionId: string) => {
    try {
      set({ isLoading: true });
      const response = await api.post('/auth/session', { session_id: sessionId });
      const user = response.data;
      
      // Store token if provided in response
      if (response.headers['set-cookie']) {
        // Cookie will be handled by the browser
      }
      
      // For mobile, we need to extract and store the token
      const token = response.data.session_token || sessionId;
      await AsyncStorage.setItem('session_token', token);
      await AsyncStorage.setItem('user', JSON.stringify(user));
      
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      // Ignore errors
    } finally {
      await AsyncStorage.removeItem('session_token');
      await AsyncStorage.removeItem('user');
      set({ user: null, isAuthenticated: false });
    }
  },

  setUser: (user) => set({ user, isAuthenticated: !!user }),
}));
