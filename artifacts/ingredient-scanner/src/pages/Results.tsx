import { useState, useRef } from "react";
import { useLocation } from "wouter";
import { useScanContext } from "../context/ScanContext";
import { useSaveHistory } from "@workspace/api-client-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import {
  ArrowLeft, Save, AlertCircle, Info, CheckCircle2,
  AlertTriangle, HelpCircle, Download, Lightbulb, ShieldCheck, ShieldAlert, ShieldX
} from "lucide-react";

export default function Results() {
  const [, setLocation] = useLocation();
  const { scanResult, lastScanText, lastProfile } = useScanContext();
  const { toast } = useToast();
  const saveMutation = useSaveHistory();
  const reportRef = useRef<HTMLDivElement>(null);

  const [isSaveOpen, setIsSaveOpen] = useState(false);
  const [productName, setProductName] = useState("");
  const [isExporting, setIsExporting] = useState(false);

  if (!scanResult) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
        <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center">
          <Info className="w-8 h-8 text-muted-foreground" />
        </div>
        <h2 className="text-xl font-semibold">No active scan results</h2>
        <p className="text-muted-foreground">Please run a scan to see results here.</p>
        <Button onClick={() => setLocation("/")} variant="outline" className="mt-4">
          <ArrowLeft className="w-4 h-4 mr-2" />Back to Scanner
        </Button>
      </div>
    );
  }

  const handleSave = () => {
    if (!productName.trim()) {
      toast({ title: "Name required", description: "Please enter a product name.", variant: "destructive" });
      return;
    }
    saveMutation.mutate(
      { data: { productName, rawText: lastScanText, grade: scanResult.grade, riskScore: scanResult.riskScore, profile: lastProfile, resultJson: JSON.stringify(scanResult) } },
      {
        onSuccess: () => {
          toast({ title: "Saved successfully", description: "The scan has been saved to your history." });
          setIsSaveOpen(false);
          setLocation("/history");
        },
        onError: () => {
          toast({ title: "Failed to save", variant: "destructive" });
        },
      }
    );
  };

  const handleExportPdf = async () => {
    if (!reportRef.current) return;
    setIsExporting(true);
    try {
      const { default: jsPDF } = await import("jspdf");
      const { default: html2canvas } = await import("html2canvas");
      const canvas = await html2canvas(reportRef.current, {
        scale: 1.5,
        useCORS: true,
        backgroundColor: "#ffffff",
        logging: false,
      });
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
      const pageHeight = pdf.internal.pageSize.getHeight();
      let y = 0;
      while (y < pdfHeight) {
        if (y > 0) pdf.addPage();
        pdf.addImage(imgData, "PNG", 0, -y, pdfWidth, pdfHeight);
        y += pageHeight;
      }
      pdf.save(`SafeScan-Report-${productName || "scan"}.pdf`);
      toast({ title: "Report downloaded", description: "PDF report saved to your device." });
    } catch {
      toast({ title: "Export failed", description: "Could not generate PDF. Try again.", variant: "destructive" });
    } finally {
      setIsExporting(false);
    }
  };

  const getGradeColor = (grade: string) => {
    const map: Record<string, string> = { A: "bg-risk-low text-white", B: "bg-emerald-500 text-white", C: "bg-risk-medium text-black", D: "bg-orange-500 text-white", F: "bg-risk-high text-white" };
    return map[grade] ?? "bg-muted text-muted-foreground";
  };

  const getGradeLabel = (grade: string) => {
    const map: Record<string, string> = { A: "Excellent", B: "Good", C: "Fair", D: "Poor", F: "Unsafe" };
    return map[grade] ?? "Unknown";
  };

  const getRiskIcon = (level: string) => {
    if (level === "high") return <AlertCircle className="w-5 h-5 text-risk-high flex-shrink-0" />;
    if (level === "medium") return <AlertTriangle className="w-5 h-5 text-risk-medium flex-shrink-0" />;
    if (level === "low") return <CheckCircle2 className="w-5 h-5 text-risk-low flex-shrink-0" />;
    return <HelpCircle className="w-5 h-5 text-muted-foreground flex-shrink-0" />;
  };

  const getRiskColorClass = (level: string) => {
    if (level === "high") return "bg-risk-high/10 border-risk-high/25";
    if (level === "medium") return "bg-risk-medium/10 border-risk-medium/25";
    if (level === "low") return "bg-risk-low/10 border-risk-low/20";
    return "bg-muted/50 border-border";
  };

  // ── Recommendations engine ──────────────────────────────────────────────────
  const generateRecommendations = () => {
    const recs: { icon: JSX.Element; type: "danger" | "warning" | "tip"; text: string }[] = [];
    const profile = lastProfile;
    const highItems = scanResult.ingredients.filter((i) => i.riskLevel === "high");
    const medItems = scanResult.ingredients.filter((i) => i.riskLevel === "medium");
    const highNames = highItems.map((i) => i.matched?.name || i.raw).slice(0, 3);
    const medNames = medItems.map((i) => i.matched?.name || i.raw).slice(0, 2);

    // Grade-based recommendation
    if (scanResult.grade === "F") {
      recs.push({ icon: <ShieldX className="w-4 h-4" />, type: "danger", text: "This product has a very high risk profile. We strongly recommend avoiding it or consulting a health professional before use." });
    } else if (scanResult.grade === "D") {
      recs.push({ icon: <ShieldAlert className="w-4 h-4" />, type: "danger", text: "This product contains several concerning ingredients. Limit consumption and look for safer alternatives." });
    } else if (scanResult.grade === "C") {
      recs.push({ icon: <AlertTriangle className="w-4 h-4" />, type: "warning", text: "Moderate risk detected. Occasional use may be acceptable, but frequent consumption is not recommended." });
    } else if (scanResult.grade === "A" || scanResult.grade === "B") {
      recs.push({ icon: <ShieldCheck className="w-4 h-4" />, type: "tip", text: "This product has a good safety profile. Most ingredients are low-risk for general adult use." });
    }

    // High-risk specific ingredients
    if (highNames.length > 0) {
      recs.push({ icon: <AlertCircle className="w-4 h-4" />, type: "danger", text: `High-risk ingredients found: ${highNames.join(", ")}. Check for safer product alternatives that omit these additives.` });
    }

    // Medium-risk
    if (medNames.length > 0) {
      recs.push({ icon: <AlertTriangle className="w-4 h-4" />, type: "warning", text: `Medium-risk ingredients detected: ${medNames.join(", ")}. These are generally safe in small amounts but worth monitoring.` });
    }

    // Profile-specific advice
    if (profile === "children") {
      const childRisk = scanResult.ingredients.filter((i) => i.warning?.toLowerCase().includes("children"));
      if (childRisk.length > 0) {
        recs.push({ icon: <AlertCircle className="w-4 h-4" />, type: "danger", text: `${childRisk.length} ingredient(s) are specifically flagged as unsafe for children. Do not give this product to infants or young children.` });
      }
      const syntheticDyes = scanResult.ingredients.filter((i) => i.matched?.category === "Colorant" && i.riskLevel === "high");
      if (syntheticDyes.length > 0) {
        recs.push({ icon: <Lightbulb className="w-4 h-4" />, type: "tip", text: "Synthetic dyes found. Research links these to hyperactivity in children. Choose products with natural colorings instead." });
      }
    }

    if (profile === "pregnant") {
      const pregRisk = scanResult.ingredients.filter((i) => i.warning?.toLowerCase().includes("pregnancy") || i.warning?.toLowerCase().includes("pregnant"));
      if (pregRisk.length > 0) {
        recs.push({ icon: <AlertCircle className="w-4 h-4" />, type: "danger", text: `${pregRisk.length} ingredient(s) require caution during pregnancy. Consult your doctor before consuming this product.` });
      }
    }

    if (profile === "elderly") {
      const eldRisk = scanResult.ingredients.filter((i) => i.warning?.toLowerCase().includes("elderly"));
      if (eldRisk.length > 0) {
        recs.push({ icon: <AlertTriangle className="w-4 h-4" />, type: "warning", text: `${eldRisk.length} ingredient(s) flagged for elderly individuals. These may interact with medications or stress kidney/liver function.` });
      }
    }

    if (profile === "allergen") {
      const allergens = scanResult.ingredients.filter((i) =>
        i.matched?.safetyNotes?.toLowerCase().includes("allerg") ||
        i.matched?.name?.toLowerCase().includes("soy") ||
        i.matched?.name?.toLowerCase().includes("wheat") ||
        i.matched?.name?.toLowerCase().includes("milk") ||
        i.matched?.name?.toLowerCase().includes("nut")
      );
      if (allergens.length > 0) {
        recs.push({ icon: <AlertCircle className="w-4 h-4" />, type: "danger", text: `Potential allergens detected: ${allergens.map(a => a.matched?.name || a.raw).slice(0, 3).join(", ")}. Avoid if you have known sensitivities.` });
      }
    }

    // Preservatives tip
    const preservatives = scanResult.ingredients.filter((i) => i.matched?.category === "Preservative");
    if (preservatives.length >= 2) {
      recs.push({ icon: <Lightbulb className="w-4 h-4" />, type: "tip", text: `${preservatives.length} preservatives found. Look for fresher alternatives with fewer chemical additives or shorter ingredient lists.` });
    }

    // E-number tip
    const eCodes = scanResult.ingredients.filter((i) => (i as unknown as { decodedCode?: string }).decodedCode);
    if (eCodes.length > 0) {
      recs.push({ icon: <Lightbulb className="w-4 h-4" />, type: "tip", text: `${eCodes.length} chemical code(s) (E-numbers/INS/CI) were identified and decoded. Always check these codes on labels — they often hide high-risk additives.` });
    }

    return recs;
  };

  const recommendations = generateRecommendations();

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pb-10">
      {/* Action bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => setLocation("/")} className="text-muted-foreground" data-testid="button-new-scan">
          <ArrowLeft className="w-4 h-4 mr-2" />New Scan
        </Button>
        <div className="flex gap-2 w-full sm:w-auto">
          <Button variant="outline" size="sm" onClick={handleExportPdf} disabled={isExporting} className="flex-1 sm:flex-none" data-testid="button-export-pdf">
            {isExporting ? <><AlertCircle className="w-4 h-4 mr-2 animate-pulse" />Generating...</> : <><Download className="w-4 h-4 mr-2" />Download PDF</>}
          </Button>
          <Button size="sm" onClick={() => setIsSaveOpen(true)} className="flex-1 sm:flex-none shadow-sm" data-testid="button-save-history">
            <Save className="w-4 h-4 mr-2" />Save to History
          </Button>
        </div>
      </div>

      {/* Printable report area */}
      <div ref={reportRef} className="space-y-6">
        {/* Grade + Breakdown */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="p-6 md:col-span-1 flex flex-col items-center justify-center text-center space-y-3 border-2 shadow-sm" data-testid="card-grade">
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">Safety Grade</div>
            <div className={`w-28 h-28 rounded-full flex items-center justify-center text-6xl font-extrabold shadow-inner ${getGradeColor(scanResult.grade)}`}>
              {scanResult.grade}
            </div>
            <div>
              <p className="font-bold text-lg">{getGradeLabel(scanResult.grade)}</p>
              <p className="text-sm text-muted-foreground">Risk Score: {scanResult.riskScore}/100</p>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed max-w-[180px]">{scanResult.summary}</p>
          </Card>

          <Card className="p-6 md:col-span-2 space-y-5 shadow-sm">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-semibold text-lg">Risk Breakdown</h3>
              <Badge variant="outline" className="px-3 py-1 bg-secondary text-secondary-foreground font-medium capitalize">
                Profile: {lastProfile}
              </Badge>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
              <div className="bg-risk-high/10 rounded-xl p-4 border border-risk-high/10" data-testid="count-high">
                <div className="text-3xl font-bold text-risk-high">{scanResult.highCount || 0}</div>
                <div className="text-xs font-semibold text-muted-foreground uppercase mt-1 tracking-wide">High Risk</div>
              </div>
              <div className="bg-risk-medium/10 rounded-xl p-4 border border-risk-medium/10" data-testid="count-medium">
                <div className="text-3xl font-bold text-risk-medium">{scanResult.mediumCount || 0}</div>
                <div className="text-xs font-semibold text-muted-foreground uppercase mt-1 tracking-wide">Medium Risk</div>
              </div>
              <div className="bg-risk-low/10 rounded-xl p-4 border border-risk-low/10" data-testid="count-low">
                <div className="text-3xl font-bold text-risk-low">{scanResult.lowCount || 0}</div>
                <div className="text-xs font-semibold text-muted-foreground uppercase mt-1 tracking-wide">Low Risk</div>
              </div>
              <div className="bg-muted rounded-xl p-4" data-testid="count-unknown">
                <div className="text-3xl font-bold text-muted-foreground">{scanResult.unknownCount || 0}</div>
                <div className="text-xs font-semibold text-muted-foreground uppercase mt-1 tracking-wide">Unknown</div>
              </div>
            </div>

            {/* Risk bar */}
            <div className="space-y-1">
              <div className="flex h-3 rounded-full overflow-hidden gap-0.5">
                {(scanResult.highCount || 0) > 0 && (
                  <div className="bg-risk-high" style={{ flex: scanResult.highCount }} />
                )}
                {(scanResult.mediumCount || 0) > 0 && (
                  <div className="bg-risk-medium" style={{ flex: scanResult.mediumCount }} />
                )}
                {(scanResult.lowCount || 0) > 0 && (
                  <div className="bg-risk-low" style={{ flex: scanResult.lowCount }} />
                )}
                {(scanResult.unknownCount || 0) > 0 && (
                  <div className="bg-muted-foreground/30" style={{ flex: scanResult.unknownCount }} />
                )}
              </div>
              <p className="text-xs text-muted-foreground text-right">{scanResult.ingredients.length} total ingredients analyzed</p>
            </div>
          </Card>
        </div>

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <Card className="p-6 shadow-sm border-l-4 border-l-primary" data-testid="section-recommendations">
            <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-primary" />
              Recommendations
            </h3>
            <div className="space-y-3">
              {recommendations.map((rec, i) => (
                <div
                  key={i}
                  className={`flex items-start gap-3 p-3 rounded-lg border text-sm ${
                    rec.type === "danger"
                      ? "bg-risk-high/8 border-risk-high/20 text-foreground"
                      : rec.type === "warning"
                      ? "bg-risk-medium/8 border-risk-medium/20 text-foreground"
                      : "bg-primary/5 border-primary/15 text-foreground"
                  }`}
                  data-testid={`recommendation-${i}`}
                >
                  <span className={
                    rec.type === "danger" ? "text-risk-high mt-0.5 flex-shrink-0" :
                    rec.type === "warning" ? "text-risk-medium mt-0.5 flex-shrink-0" :
                    "text-primary mt-0.5 flex-shrink-0"
                  }>
                    {rec.icon}
                  </span>
                  <p className="leading-relaxed">{rec.text}</p>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Ingredient list */}
        <div className="space-y-4">
          <h3 className="font-semibold text-xl">Ingredients ({scanResult.ingredients.length})</h3>
          <div className="grid grid-cols-1 gap-3">
            {scanResult.ingredients.map((ing, i) => {
              const decoded = (ing as unknown as { decodedCode?: string }).decodedCode;
              return (
                <div
                  key={i}
                  className={`flex items-start gap-4 p-4 rounded-xl border ${getRiskColorClass(ing.riskLevel)} transition-all hover:shadow-md`}
                  data-testid={`ingredient-row-${i}`}
                >
                  <div className="mt-0.5">{getRiskIcon(ing.riskLevel)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="font-semibold text-base capitalize">
                          {ing.matched?.name || ing.raw}
                        </h4>
                        {decoded && (
                          <Badge variant="secondary" className="text-xs font-mono font-semibold">
                            {decoded}
                          </Badge>
                        )}
                      </div>
                      <Badge
                        variant="outline"
                        className={`w-fit text-xs font-semibold uppercase tracking-wider ${
                          ing.riskLevel === "high" ? "border-risk-high/30 text-risk-high bg-risk-high/10" :
                          ing.riskLevel === "medium" ? "border-risk-medium/30 text-risk-medium bg-risk-medium/10" :
                          ing.riskLevel === "low" ? "border-risk-low/30 text-risk-low bg-risk-low/10" :
                          ""
                        }`}
                      >
                        {ing.riskLevel}
                      </Badge>
                    </div>

                    {ing.matched?.category && (
                      <p className="text-xs text-muted-foreground mb-1.5 font-medium tracking-wide uppercase">
                        {ing.matched.category}
                      </p>
                    )}

                    {decoded && ing.raw !== ing.matched?.name && (
                      <p className="text-xs text-muted-foreground mb-1 font-mono">
                        Detected as: {ing.raw}
                      </p>
                    )}

                    {ing.warning ? (
                      <p className={`text-sm font-medium mt-1 p-2.5 rounded-lg border ${
                        ing.riskLevel === "high"
                          ? "text-risk-high bg-risk-high/5 border-risk-high/15"
                          : "text-risk-medium bg-risk-medium/5 border-risk-medium/15"
                      }`}>
                        {ing.warning}
                      </p>
                    ) : ing.matched?.description ? (
                      <p className="text-sm text-muted-foreground leading-relaxed mt-1">
                        {ing.matched.description}
                      </p>
                    ) : null}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Save dialog */}
      <Dialog open={isSaveOpen} onOpenChange={setIsSaveOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Save Scan Result</DialogTitle>
            <DialogDescription>Give this product a name so you can find it later in your history.</DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label htmlFor="product-name">Product Name</Label>
            <Input
              id="product-name"
              data-testid="input-product-name"
              placeholder="e.g. Maggi Noodles, Sunsilk Shampoo..."
              className="mt-2"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSave()}
              autoFocus
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsSaveOpen(false)}>Cancel</Button>
            <Button onClick={handleSave} disabled={saveMutation.isPending || !productName.trim()} data-testid="button-confirm-save">
              {saveMutation.isPending ? "Saving..." : "Save Product"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
