import React, { useState } from "react";
import { Link, useLocation } from "wouter";
import { useScanContext } from "../context/ScanContext";
import { useSaveHistory } from "@workspace/api-client-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { ArrowLeft, Save, AlertCircle, Info, CheckCircle2, AlertTriangle, HelpCircle } from "lucide-react";

export default function Results() {
  const [, setLocation] = useLocation();
  const { scanResult, lastScanText, lastProfile } = useScanContext();
  const { toast } = useToast();
  const saveMutation = useSaveHistory();
  
  const [isSaveOpen, setIsSaveOpen] = useState(false);
  const [productName, setProductName] = useState("");

  if (!scanResult) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
        <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center">
          <Info className="w-8 h-8 text-muted-foreground" />
        </div>
        <h2 className="text-xl font-semibold">No active scan results</h2>
        <p className="text-muted-foreground">Please run a scan to see results here.</p>
        <Button onClick={() => setLocation("/")} variant="outline" className="mt-4">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Scanner
        </Button>
      </div>
    );
  }

  const handleSave = () => {
    if (!productName.trim()) {
      toast({ title: "Name required", description: "Please enter a product name.", variant: "destructive" });
      return;
    }

    saveMutation.mutate({
      data: {
        productName,
        rawText: lastScanText,
        grade: scanResult.grade,
        riskScore: scanResult.riskScore,
        profile: lastProfile,
        resultJson: JSON.stringify(scanResult)
      }
    }, {
      onSuccess: () => {
        toast({ title: "Saved successfully", description: "The scan has been saved to your history." });
        setIsSaveOpen(false);
        setLocation("/history");
      },
      onError: () => {
        toast({ title: "Failed to save", description: "There was an error saving the scan.", variant: "destructive" });
      }
    });
  };

  const getGradeColor = (grade: string) => {
    switch(grade) {
      case 'A': return "bg-risk-low text-white";
      case 'B': return "bg-emerald-500 text-white";
      case 'C': return "bg-risk-medium text-black";
      case 'D': return "bg-orange-500 text-white";
      case 'F': return "bg-risk-high text-white";
      default: return "bg-muted text-muted-foreground";
    }
  };

  const getRiskIcon = (level: string) => {
    switch(level) {
      case 'high': return <AlertCircle className="w-5 h-5 text-risk-high" />;
      case 'medium': return <AlertTriangle className="w-5 h-5 text-risk-medium" />;
      case 'low': return <CheckCircle2 className="w-5 h-5 text-risk-low" />;
      default: return <HelpCircle className="w-5 h-5 text-risk-unknown" />;
    }
  };

  const getRiskColorClass = (level: string) => {
    switch(level) {
      case 'high': return "bg-risk-high/10 border-risk-high/20";
      case 'medium': return "bg-risk-medium/10 border-risk-medium/20";
      case 'low': return "bg-risk-low/10 border-risk-low/20";
      default: return "bg-muted/50 border-border";
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pb-10">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => setLocation("/")} className="text-muted-foreground">
          <ArrowLeft className="w-4 h-4 mr-2" />
          New Scan
        </Button>
        <Button onClick={() => setIsSaveOpen(true)} className="w-full sm:w-auto shadow-sm">
          <Save className="w-4 h-4 mr-2" />
          Save to History
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6 md:col-span-1 flex flex-col items-center justify-center text-center space-y-4 border-2 shadow-sm">
          <div className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Safety Grade</div>
          <div className={`w-32 h-32 rounded-full flex items-center justify-center text-6xl font-extrabold shadow-inner ${getGradeColor(scanResult.grade)}`}>
            {scanResult.grade}
          </div>
          <div className="space-y-1">
            <h3 className="font-semibold text-xl">Risk Score: {scanResult.riskScore}/100</h3>
            <p className="text-sm text-muted-foreground max-w-[200px] mx-auto">{scanResult.summary}</p>
          </div>
        </Card>

        <Card className="p-6 md:col-span-2 space-y-6 shadow-sm">
          <h3 className="font-semibold text-lg border-b pb-4">Risk Breakdown</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            <div className="bg-risk-high/10 rounded-lg p-4">
              <div className="text-3xl font-bold text-risk-high">{scanResult.highCount || 0}</div>
              <div className="text-xs font-medium text-muted-foreground uppercase mt-1">High Risk</div>
            </div>
            <div className="bg-risk-medium/10 rounded-lg p-4">
              <div className="text-3xl font-bold text-risk-medium">{scanResult.mediumCount || 0}</div>
              <div className="text-xs font-medium text-muted-foreground uppercase mt-1">Medium Risk</div>
            </div>
            <div className="bg-risk-low/10 rounded-lg p-4">
              <div className="text-3xl font-bold text-risk-low">{scanResult.lowCount || 0}</div>
              <div className="text-xs font-medium text-muted-foreground uppercase mt-1">Low Risk</div>
            </div>
            <div className="bg-muted rounded-lg p-4">
              <div className="text-3xl font-bold text-risk-unknown">{scanResult.unknownCount || 0}</div>
              <div className="text-xs font-medium text-muted-foreground uppercase mt-1">Unknown</div>
            </div>
          </div>
          <div className="pt-2">
            <Badge variant="outline" className="px-3 py-1 bg-secondary text-secondary-foreground font-medium">
              Profile: {lastProfile.charAt(0).toUpperCase() + lastProfile.slice(1)}
            </Badge>
          </div>
        </Card>
      </div>

      <div className="space-y-4">
        <h3 className="font-semibold text-xl pt-4">Ingredients ({scanResult.ingredients.length})</h3>
        <div className="grid grid-cols-1 gap-3">
          {scanResult.ingredients.map((ing, i) => (
            <div key={i} className={`flex items-start gap-4 p-4 rounded-xl border ${getRiskColorClass(ing.riskLevel)} transition-all hover:shadow-md`}>
              <div className="mt-0.5">{getRiskIcon(ing.riskLevel)}</div>
              <div className="flex-1 min-w-0">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-1">
                  <h4 className="font-semibold text-base capitalize truncate">
                    {ing.matched?.name || ing.raw}
                  </h4>
                  <Badge variant="outline" className="w-fit text-xs font-medium uppercase tracking-wider opacity-80">
                    {ing.riskLevel}
                  </Badge>
                </div>
                
                {ing.matched?.category && (
                  <p className="text-xs text-muted-foreground mb-2 font-medium">
                    {ing.matched.category}
                  </p>
                )}
                
                {ing.warning ? (
                  <p className="text-sm font-medium text-risk-high mt-1 bg-risk-high/5 p-2 rounded-md border border-risk-high/10">
                    ⚠️ {ing.warning}
                  </p>
                ) : ing.matched?.description ? (
                  <p className="text-sm text-muted-foreground leading-relaxed mt-1">
                    {ing.matched.description}
                  </p>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      </div>

      <Dialog open={isSaveOpen} onOpenChange={setIsSaveOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Save Scan Result</DialogTitle>
            <DialogDescription>
              Give this product a name so you can find it later in your history.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label htmlFor="product-name">Product Name</Label>
            <Input 
              id="product-name" 
              placeholder="e.g. My Favorite Shampoo" 
              className="mt-2"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
              autoFocus
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsSaveOpen(false)}>Cancel</Button>
            <Button onClick={handleSave} disabled={saveMutation.isPending || !productName.trim()}>
              {saveMutation.isPending ? "Saving..." : "Save Product"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
