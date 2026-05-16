import React, { createContext, useContext, useState } from 'react';
import type { ScanResult } from '@workspace/api-client-react';

interface ScanContextType {
  scanResult: ScanResult | null;
  setScanResult: (res: ScanResult | null) => void;
  lastScanText: string;
  setLastScanText: (text: string) => void;
  lastProfile: string;
  setLastProfile: (profile: string) => void;
}

const ScanContext = createContext<ScanContextType | null>(null);

export const ScanProvider = ({ children }: { children: React.ReactNode }) => {
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [lastScanText, setLastScanText] = useState("");
  const [lastProfile, setLastProfile] = useState("general");

  return (
    <ScanContext.Provider 
      value={{ 
        scanResult, setScanResult, 
        lastScanText, setLastScanText, 
        lastProfile, setLastProfile 
      }}
    >
      {children}
    </ScanContext.Provider>
  );
};

export const useScanContext = () => {
  const ctx = useContext(ScanContext);
  if (!ctx) throw new Error("useScanContext must be used within ScanProvider");
  return ctx;
};
