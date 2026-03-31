import { create } from "zustand";

interface SceneState {
  isLoading: boolean;
  terrainLoaded: boolean;
  plumeVisible: boolean;
  cameraTarget: [number, number, number] | null;
  setLoading: (loading: boolean) => void;
  setTerrainLoaded: (loaded: boolean) => void;
  setPlumeVisible: (visible: boolean) => void;
  setCameraTarget: (target: [number, number, number] | null) => void;
}

export const useSceneStore = create<SceneState>((set) => ({
  isLoading: true,
  terrainLoaded: false,
  plumeVisible: true,
  cameraTarget: null,
  setLoading: (isLoading) => set({ isLoading }),
  setTerrainLoaded: (terrainLoaded) => set({ terrainLoaded }),
  setPlumeVisible: (plumeVisible) => set({ plumeVisible }),
  setCameraTarget: (cameraTarget) => set({ cameraTarget }),
}));
