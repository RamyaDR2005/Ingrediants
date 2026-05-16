import React, { useState } from "react";
import { useLocation } from "wouter";
import { useScanIngredients, ScanInputProfile } from "@workspace/api-client-react";
import { useScanContext } from "../context/ScanContext";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Loader2, ShieldCheck, AlertTriangle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export default function Home() {
  const [location, setLocation] = useLocation();
  const { setScanResult, lastScanText, setLastScanText, lastProfile, setLastProfile } = useScanContext();
  const { toast } = useToast();
  
  const scanMutation = useScanIngredients();

  const handleScan = () => {
    if (!lastScanText.trim()) {
      toast({
        title: "Please enter ingredients",
        description: "You must provide an ingredient list to analyze.",
        variant: "destructive"
      });
      return;
    }

    scanMutation.mutate({
      data: {
        text: lastScanText,
        profile: lastProfile as ScanInputProfile
      }
    }, {
      onSuccess: (data) => {
        setScanResult(data);
        setLocation("/results");
      },
      onError: (err) => {
        toast({
          title: "Analysis failed",
          description: "There was an error analyzing the ingredients.",
          variant: "destructive"
        });
      }
    });
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="space-y-3 text-center md:text-left">
        <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground">
          Analyze Product Safety
        </h1>
        <p className="text-muted-foreground text-lg max-w-2xl leading-relaxed">
          Paste an ingredient list from any food, cosmetic, or supplement. We'll identify hidden risks, allergens, and safety concerns instantly.
        </p>
      </div>

      <div className="bg-card rounded-xl border shadow-sm p-1">
        <div className="p-4 md:p-6 space-y-6">
          <div className="space-y-3">
            <Label htmlFor="ingredients" className="text-base font-semibold">Ingredient List</Label>
            <Textarea
              id="ingredients"
              placeholder="e.g. Water, Cetearyl Alcohol, Glycerin, Phenoxyethanol, Parabens, Fragrance..."
              className="min-h-[200px] text-base resize-y bg-background border-muted p-4 focus-visible:ring-primary focus-visible:border-primary shadow-inner"
              value={lastScanText}
              onChange={(e) => setLastScanText(e.target.value)}
            />
          </div>

          <div className="flex flex-col md:flex-row gap-4 items-end">
            <div className="space-y-3 w-full md:w-1/2">
              <Label htmlFor="profile" className="text-sm font-semibold text-muted-foreground">Safety Profile</Label>
              <Select value={lastProfile} onValueChange={setLastProfile}>
                <SelectTrigger id="profile" className="h-12 bg-background">
                  <SelectValue placeholder="Select a profile" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="general">General Adult</SelectItem>
                  <SelectItem value="children">Children & Infants</SelectItem>
                  <SelectItem value="pregnant">Pregnancy</SelectItem>
                  <SelectItem value="elderly">Elderly</SelectItem>
                  <SelectItem value="allergen">Allergen Sensitive</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <Button 
              size="lg" 
              className="w-full md:w-auto h-12 px-8 text-base font-semibold shadow-md transition-transform active:scale-[0.98]"
              onClick={handleScan}
              disabled={scanMutation.isPending || !lastScanText.trim()}
            >
              {scanMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <ShieldCheck className="mr-2 h-5 w-5" />
                  Analyze Ingredients
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
        <div className="p-5 rounded-xl bg-secondary/50 border border-secondary">
          <ShieldCheck className="w-8 h-8 text-primary mb-3" />
          <h3 className="font-semibold mb-1">1,200+ Database</h3>
          <p className="text-sm text-muted-foreground">Checked against a comprehensive library of known substances.</p>
        </div>
        <div className="p-5 rounded-xl bg-secondary/50 border border-secondary">
          <AlertTriangle className="w-8 h-8 text-amber-500 mb-3" />
          <h3 className="font-semibold mb-1">Risk Detection</h3>
          <p className="text-sm text-muted-foreground">Instantly highlights high-risk chemicals, preservatives, and toxins.</p>
        </div>
        <div className="p-5 rounded-xl bg-secondary/50 border border-secondary">
          <svg className="w-8 h-8 text-blue-500 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <h3 className="font-semibold mb-1">Custom Profiles</h3>
          <p className="text-sm text-muted-foreground">Tailor results for pregnancy, children, or specific allergies.</p>
        </div>
      </div>
    </div>
  );
}
