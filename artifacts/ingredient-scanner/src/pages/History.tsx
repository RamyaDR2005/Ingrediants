import React from "react";
import { Link, useLocation } from "wouter";
import { 
  useListHistory, 
  useDeleteHistory,
  getListHistoryQueryKey
} from "@workspace/api-client-react";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Trash2, ArrowRight, History as HistoryIcon } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { format } from "date-fns";
import { useScanContext } from "../context/ScanContext";

export default function History() {
  const [, setLocation] = useLocation();
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const { setScanResult } = useScanContext();

  const { data: history, isLoading } = useListHistory({ limit: 50 }, {
    query: {
      queryKey: getListHistoryQueryKey({ limit: 50 })
    }
  });

  const deleteMutation = useDeleteHistory();

  const handleDelete = (id: number) => {
    if (!confirm("Are you sure you want to delete this scan?")) return;
    
    deleteMutation.mutate({ id }, {
      onSuccess: () => {
        toast({ title: "Scan deleted" });
        queryClient.invalidateQueries({ queryKey: getListHistoryQueryKey({ limit: 50 }) });
      },
      onError: () => {
        toast({ title: "Failed to delete", variant: "destructive" });
      }
    });
  };

  const handleView = (entry: any) => {
    if (entry.resultJson) {
      try {
        const result = JSON.parse(entry.resultJson);
        setScanResult(result);
        setLocation("/results");
      } catch (e) {
        toast({ title: "Failed to parse result", variant: "destructive" });
      }
    }
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

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pb-10">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">Scan History</h1>
        <p className="text-muted-foreground">Review your previously saved product analyses.</p>
      </div>

      {isLoading ? (
        <div className="flex flex-col items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-primary mb-4" />
          <p className="text-muted-foreground">Loading history...</p>
        </div>
      ) : history?.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 bg-card rounded-xl border border-dashed space-y-4">
          <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center">
            <HistoryIcon className="w-8 h-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold">No history yet</h3>
          <p className="text-muted-foreground text-center max-w-sm">
            You haven't saved any product scans yet. Scan a product and click "Save to History" to see it here.
          </p>
          <Button onClick={() => setLocation("/")}>Go to Scanner</Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {history?.map((entry) => (
            <Card key={entry.id} className="flex flex-col overflow-hidden hover:shadow-md transition-shadow">
              <div className="p-5 flex-1 space-y-4">
                <div className="flex justify-between items-start">
                  <div className="space-y-1">
                    <h3 className="font-semibold text-lg line-clamp-1" title={entry.productName}>
                      {entry.productName}
                    </h3>
                    <p className="text-xs text-muted-foreground">
                      {format(new Date(entry.createdAt), "MMM d, yyyy • h:mm a")}
                    </p>
                  </div>
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg shadow-sm ${getGradeColor(entry.grade)}`}>
                    {entry.grade}
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="bg-secondary/50">
                    Risk Score: {entry.riskScore}/100
                  </Badge>
                  {entry.profile && entry.profile !== "general" && (
                    <Badge variant="outline" className="capitalize">
                      {entry.profile}
                    </Badge>
                  )}
                </div>
              </div>
              
              <div className="bg-muted/30 border-t p-3 flex justify-between items-center">
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                  onClick={() => handleDelete(entry.id)}
                  disabled={deleteMutation.isPending}
                >
                  <Trash2 className="w-4 h-4 mr-1.5" />
                  Delete
                </Button>
                
                <Button 
                  size="sm" 
                  className="pl-3 pr-2"
                  onClick={() => handleView(entry)}
                  disabled={!entry.resultJson}
                >
                  View Details
                  <ArrowRight className="w-4 h-4 ml-1.5" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
