import React from "react";
import { useParams, Link, useLocation } from "wouter";
import { useGetIngredient, getGetIngredientQueryKey } from "@workspace/api-client-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Loader2, AlertTriangle, Info, BookOpen, Tag } from "lucide-react";

export default function IngredientDetail() {
  const params = useParams();
  const id = parseInt(params.id || "0", 10);
  const [, setLocation] = useLocation();

  const { data: ingredient, isLoading, isError } = useGetIngredient(id, {
    query: {
      queryKey: getGetIngredientQueryKey(id),
      enabled: !!id
    }
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <p className="text-muted-foreground">Loading ingredient details...</p>
      </div>
    );
  }

  if (isError || !ingredient) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
        <AlertTriangle className="w-12 h-12 text-destructive" />
        <h2 className="text-xl font-bold">Ingredient Not Found</h2>
        <p className="text-muted-foreground">The requested ingredient could not be found in our database.</p>
        <Button onClick={() => setLocation("/database")} variant="outline" className="mt-4">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Database
        </Button>
      </div>
    );
  }

  const getRiskColorClass = (level: string) => {
    switch(level) {
      case 'high': return "bg-risk-high text-white";
      case 'medium': return "bg-risk-medium text-black";
      case 'low': return "bg-risk-low text-white";
      default: return "bg-muted text-muted-foreground";
    }
  };

  const getRiskBgClass = (level: string) => {
    switch(level) {
      case 'high': return "bg-risk-high/10 border-risk-high/20";
      case 'medium': return "bg-risk-medium/10 border-risk-medium/20";
      case 'low': return "bg-risk-low/10 border-risk-low/20";
      default: return "bg-muted border-border";
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-4xl mx-auto pb-10">
      <Button variant="ghost" size="sm" onClick={() => window.history.back()} className="text-muted-foreground -ml-2">
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back
      </Button>

      <div className={`p-6 md:p-8 rounded-2xl border ${getRiskBgClass(ingredient.riskLevel)} shadow-sm`}>
        <div className="flex flex-col md:flex-row justify-between items-start gap-4 mb-4">
          <div className="space-y-1.5">
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-foreground capitalize">
              {ingredient.name}
            </h1>
            {ingredient.code && (
              <p className="text-lg font-mono text-muted-foreground">{ingredient.code}</p>
            )}
          </div>
          <Badge className={`text-base px-4 py-1.5 rounded-full capitalize font-semibold shadow-sm ${getRiskColorClass(ingredient.riskLevel)}`}>
            {ingredient.riskLevel} Risk
          </Badge>
        </div>

        {ingredient.category && (
          <div className="flex items-center gap-2 mt-4 text-sm font-medium bg-background/50 w-fit px-3 py-1.5 rounded-md border border-border/50">
            <Tag className="w-4 h-4 text-primary" />
            <span>Category: {ingredient.category}</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="shadow-sm">
          <CardHeader className="bg-muted/30 border-b">
            <CardTitle className="flex items-center gap-2 text-lg">
              <BookOpen className="w-5 h-5 text-primary" />
              Description
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            {ingredient.description ? (
              <p className="text-foreground leading-relaxed">{ingredient.description}</p>
            ) : (
              <p className="text-muted-foreground italic">No detailed description available for this ingredient.</p>
            )}
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardHeader className="bg-muted/30 border-b">
            <CardTitle className="flex items-center gap-2 text-lg">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              Safety Notes & Warnings
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            {ingredient.safetyNotes ? (
              <p className="text-foreground leading-relaxed">{ingredient.safetyNotes}</p>
            ) : (
              <p className="text-muted-foreground italic">No specific safety warnings documented.</p>
            )}

            {ingredient.profileFlags && (
              <div className="mt-6 space-y-2">
                <h4 className="font-semibold text-sm uppercase tracking-wider text-muted-foreground">Sensitive Profiles</h4>
                <div className="flex flex-wrap gap-2">
                  {ingredient.profileFlags.split(',').map((flag) => (
                    <Badge key={flag.trim()} variant="secondary" className="capitalize bg-secondary text-secondary-foreground">
                      {flag.trim()}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            
            {ingredient.source && (
              <div className="mt-6 pt-4 border-t border-border/50 space-y-1">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Source / Designation</h4>
                <p className="text-sm font-medium">{ingredient.source}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
