import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface UserPreferences {
  defaultCoverLetterStyle: 'standard' | 'executive' | 'ultra-tight'
  autoDownloadAfterGenerate: boolean
}

interface UserState {
  userId: number
  preferences: UserPreferences

  setUserId: (id: number) => void
  updatePreferences: (prefs: Partial<UserPreferences>) => void
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      userId: 1, // Default user ID for single-user mode
      preferences: {
        defaultCoverLetterStyle: 'standard',
        autoDownloadAfterGenerate: false,
      },

      setUserId: (id) => set({ userId: id }),
      updatePreferences: (prefs) =>
        set((state) => ({
          preferences: { ...state.preferences, ...prefs }
        })),
    }),
    {
      name: 'etps-user-storage',
    }
  )
)
