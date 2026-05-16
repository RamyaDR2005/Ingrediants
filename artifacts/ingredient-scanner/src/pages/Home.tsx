import { useState, useRef, useCallback } from "react";
import { useLocation } from "wouter";
import { useScanIngredients, ScanInputProfile } from "@workspace/api-client-react";
import { useScanContext } from "../context/ScanContext";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Loader2, ShieldCheck, AlertTriangle, Upload, Image, FileText, X, ScanLine } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export default function Home() {
  const [, setLocation] = useLocation();
  const { setScanResult, lastScanText, setLastScanText, lastProfile, setLastProfile } = useScanContext();
  const { toast } = useToast();

  const [activeTab, setActiveTab] = useState<"text" | "image">("text");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [isOcrRunning, setIsOcrRunning] = useState(false);
  const [ocrProgress, setOcrProgress] = useState(0);
  const [extractedText, setExtractedText] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropRef = useRef<HTMLDivElement>(null);

  const scanMutation = useScanIngredients();

  const handleFileSelect = async (file: File) => {
    if (!file.type.startsWith("image/")) {
      toast({ title: "Invalid file", description: "Please upload an image file (JPG, PNG, etc.)", variant: "destructive" });
      return;
    }
    setImageFile(file);
    const url = URL.createObjectURL(file);
    setImagePreview(url);
    setExtractedText("");
    await runOcr(file);
  };

  const runOcr = async (file: File) => {
    setIsOcrRunning(true);
    setOcrProgress(0);
    try {
      // Dynamically import Tesseract to keep initial bundle small
      const { createWorker } = await import("tesseract.js");
      const worker = await createWorker("eng", 1, {
        logger: (m: { status: string; progress: number }) => {
          if (m.status === "recognizing text") {
            setOcrProgress(Math.round(m.progress * 100));
          }
        },
      });
      const { data: { text } } = await worker.recognize(file);
      await worker.terminate();

      // Extract ingredient section from OCR text
      const extracted = extractIngredientSection(text);
      setExtractedText(extracted);
      setLastScanText(extracted);
      toast({
        title: "Text extracted from image",
        description: "Review the extracted ingredients below, then click Analyze.",
      });
    } catch {
      toast({
        title: "OCR failed",
        description: "Could not extract text from image. Try a clearer photo or paste the text manually.",
        variant: "destructive",
      });
    } finally {
      setIsOcrRunning(false);
      setOcrProgress(0);
    }
  };

  function extractIngredientSection(rawText: string): string {
    // Try to find the "Ingredients:" section
    const lower = rawText.toLowerCase();
    const idx = lower.search(/ingredients?\s*[:：]/i);
    if (idx !== -1) {
      const after = rawText.slice(idx);
      // Take text until a new section heading or end
      const sectionEnd = after.search(/\n[A-Z][A-Z\s]{4,}:/);
      return (sectionEnd > 20 ? after.slice(0, sectionEnd) : after)
        .replace(/^ingredients?\s*[:：]\s*/i, "")
        .trim();
    }
    // Fallback: return cleaned full text
    return rawText.replace(/\n{3,}/g, "\n").trim();
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  }, []);

  const handleScan = () => {
    const textToScan = activeTab === "image" ? extractedText : lastScanText;
    if (!textToScan.trim()) {
      toast({
        title: activeTab === "image" ? "No text extracted yet" : "Please enter ingredients",
        description: activeTab === "image"
          ? "Upload a product label image and wait for text extraction to complete."
          : "You must provide an ingredient list to analyze.",
        variant: "destructive",
      });
      return;
    }

    scanMutation.mutate(
      { data: { text: textToScan, profile: lastProfile as ScanInputProfile } },
      {
        onSuccess: (data) => {
          setScanResult(data);
          if (activeTab === "image") setLastScanText(textToScan);
          setLocation("/results");
        },
        onError: () => {
          toast({ title: "Analysis failed", description: "There was an error analyzing the ingredients.", variant: "destructive" });
        },
      }
    );
  };

  const clearImage = () => {
    setImageFile(null);
    setImagePreview(null);
    setExtractedText("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="space-y-3 text-center md:text-left">
        <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground">
          Analyze Product Safety
        </h1>
        <p className="text-muted-foreground text-lg max-w-2xl leading-relaxed">
          Upload a product label photo or paste an ingredient list. We'll identify hidden risks, chemical codes, and safety concerns instantly.
        </p>
      </div>

      <div className="bg-card rounded-xl border shadow-sm">
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "text" | "image")} className="w-full">
          <div className="px-4 pt-4 md:px-6 md:pt-6">
            <TabsList className="grid w-full grid-cols-2 mb-6" data-testid="input-tabs">
              <TabsTrigger value="text" className="gap-2" data-testid="tab-text">
                <FileText className="w-4 h-4" />
                Paste Text
              </TabsTrigger>
              <TabsTrigger value="image" className="gap-2" data-testid="tab-image">
                <ScanLine className="w-4 h-4" />
                Scan Label (OCR)
              </TabsTrigger>
            </TabsList>
          </div>

          {/* TEXT TAB */}
          <TabsContent value="text" className="px-4 pb-6 md:px-6 space-y-4 mt-0">
            <div className="space-y-2">
              <Label htmlFor="ingredients" className="text-base font-semibold">Ingredient List</Label>
              <Textarea
                id="ingredients"
                data-testid="textarea-ingredients"
                placeholder={"e.g. Water, Sugar, E211, Sodium Benzoate, E102 (Tartrazine), CI 16035, Citric Acid, Natural Flavors..."}
                className="min-h-[200px] text-base resize-y bg-background border-muted p-4 focus-visible:ring-primary focus-visible:border-primary shadow-inner"
                value={lastScanText}
                onChange={(e) => setLastScanText(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Supports E-numbers (E211), INS codes (INS 110), CI codes (CI 16035), and common ingredient names.
              </p>
            </div>
          </TabsContent>

          {/* IMAGE / OCR TAB */}
          <TabsContent value="image" className="px-4 pb-6 md:px-6 space-y-4 mt-0">
            {!imageFile ? (
              <div
                ref={dropRef}
                onDrop={handleDrop}
                onDragOver={(e) => e.preventDefault()}
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-muted-foreground/30 rounded-xl p-10 text-center cursor-pointer hover:border-primary/50 hover:bg-primary/5 transition-all group"
                data-testid="drop-zone"
              >
                <Upload className="w-12 h-12 text-muted-foreground/40 group-hover:text-primary/60 mx-auto mb-4 transition-colors" />
                <p className="font-semibold text-foreground mb-1">Drop your product label here</p>
                <p className="text-sm text-muted-foreground mb-4">or click to browse — JPG, PNG, WebP supported</p>
                <Button variant="outline" size="sm" type="button" className="pointer-events-none">
                  <Image className="w-4 h-4 mr-2" />
                  Choose Image
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                  data-testid="input-file"
                />
              </div>
            ) : (
              <div className="space-y-4">
                <div className="relative rounded-xl overflow-hidden border bg-muted/30">
                  <img
                    src={imagePreview!}
                    alt="Product label"
                    className="w-full max-h-64 object-contain"
                    data-testid="img-preview"
                  />
                  <button
                    onClick={clearImage}
                    className="absolute top-2 right-2 bg-black/60 hover:bg-black/80 text-white rounded-full p-1.5 transition-colors"
                    data-testid="button-clear-image"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {isOcrRunning && (
                  <div className="space-y-2 p-4 bg-primary/5 rounded-lg border border-primary/10">
                    <div className="flex items-center gap-2 text-sm font-medium text-primary">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Extracting text from image... {ocrProgress}%
                    </div>
                    <div className="w-full bg-muted rounded-full h-1.5">
                      <div
                        className="bg-primary h-1.5 rounded-full transition-all duration-300"
                        style={{ width: `${ocrProgress}%` }}
                      />
                    </div>
                  </div>
                )}

                {extractedText && !isOcrRunning && (
                  <div className="space-y-2">
                    <Label className="text-sm font-semibold">Extracted Ingredients (review & edit if needed)</Label>
                    <Textarea
                      value={extractedText}
                      onChange={(e) => setExtractedText(e.target.value)}
                      className="min-h-[120px] text-sm resize-y bg-background font-mono"
                      data-testid="textarea-ocr-result"
                    />
                    <p className="text-xs text-muted-foreground">
                      OCR results may have minor errors. You can correct them before analyzing.
                    </p>
                  </div>
                )}
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Profile + Analyze (shared) */}
        <div className="px-4 pb-6 md:px-6">
          <div className="flex flex-col md:flex-row gap-4 items-end pt-2 border-t">
            <div className="space-y-2 w-full md:w-1/2 pt-4">
              <Label htmlFor="profile" className="text-sm font-semibold text-muted-foreground">Safety Profile</Label>
              <Select value={lastProfile} onValueChange={setLastProfile}>
                <SelectTrigger id="profile" className="h-12 bg-background" data-testid="select-profile">
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
              className="w-full md:w-auto h-12 px-8 text-base font-semibold shadow-md transition-transform active:scale-[0.98] mt-4"
              onClick={handleScan}
              disabled={scanMutation.isPending || isOcrRunning}
              data-testid="button-analyze"
            >
              {scanMutation.isPending ? (
                <><Loader2 className="mr-2 h-5 w-5 animate-spin" />Analyzing...</>
              ) : (
                <><ShieldCheck className="mr-2 h-5 w-5" />Analyze Ingredients</>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Feature cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
        <div className="p-5 rounded-xl bg-secondary/50 border border-secondary">
          <ScanLine className="w-8 h-8 text-primary mb-3" />
          <h3 className="font-semibold mb-1">OCR Label Scanning</h3>
          <p className="text-sm text-muted-foreground">Photograph any product label and extract ingredients automatically.</p>
        </div>
        <div className="p-5 rounded-xl bg-secondary/50 border border-secondary">
          <AlertTriangle className="w-8 h-8 text-amber-500 mb-3" />
          <h3 className="font-semibold mb-1">Code Detection</h3>
          <p className="text-sm text-muted-foreground">Decodes E-numbers, INS codes, and CI color codes into plain English.</p>
        </div>
        <div className="p-5 rounded-xl bg-secondary/50 border border-secondary">
          <ShieldCheck className="w-8 h-8 text-primary mb-3" />
          <h3 className="font-semibold mb-1">Smart Recommendations</h3>
          <p className="text-sm text-muted-foreground">Personalized safety advice for your specific health profile.</p>
        </div>
      </div>
    </div>
  );
}
