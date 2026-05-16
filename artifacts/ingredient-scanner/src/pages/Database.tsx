import React, { useState } from "react";
import { Link } from "wouter";
import { 
  useListIngredients, 
  getListIngredientsQueryKey,
  ListIngredientsRiskLevel 
} from "@workspace/api-client-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Search, Loader2, Filter } from "lucide-react";
import { useDebounce } from "@/hooks/use-debounce";

// Simple debounce hook for local use if not in hooks/
function useLocalDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  React.useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

export default function Database() {
  const [search, setSearch] = useState("");
  const debouncedSearch = useLocalDebounce(search, 500);
  const [riskLevel, setRiskLevel] = useState<string>("all");
  const [page, setPage] = useState(1);
  const limit = 20;

  const params = {
    limit,
    offset: (page - 1) * limit,
    ...(debouncedSearch ? { search: debouncedSearch } : {}),
    ...(riskLevel !== "all" ? { riskLevel: riskLevel as ListIngredientsRiskLevel } : {})
  };

  const { data: ingredients, isLoading, isError } = useListIngredients(params, {
    query: {
      queryKey: getListIngredientsQueryKey(params),
      keepPreviousData: true
    }
  });

  const getRiskColor = (level: string) => {
    switch(level) {
      case 'high': return "bg-risk-high text-white hover:bg-risk-high/90";
      case 'medium': return "bg-risk-medium text-black hover:bg-risk-medium/90";
      case 'low': return "bg-risk-low text-white hover:bg-risk-low/90";
      default: return "bg-muted text-muted-foreground";
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pb-10">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight">Ingredient Database</h1>
          <p className="text-muted-foreground">Browse and search the complete repository of analyzed ingredients.</p>
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center bg-card p-4 rounded-xl border shadow-sm">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input 
            placeholder="Search by name, code, or function..." 
            className="pl-9 h-10"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
          />
        </div>
        <div className="flex items-center gap-2 w-full md:w-auto">
          <Filter className="w-4 h-4 text-muted-foreground" />
          <Select 
            value={riskLevel} 
            onValueChange={(val) => {
              setRiskLevel(val);
              setPage(1);
            }}
          >
            <SelectTrigger className="w-full md:w-[180px] h-10">
              <SelectValue placeholder="Filter by Risk" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Risk Levels</SelectItem>
              <SelectItem value="high">High Risk</SelectItem>
              <SelectItem value="medium">Medium Risk</SelectItem>
              <SelectItem value="low">Low Risk</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="bg-card rounded-xl border shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50 hover:bg-muted/50">
                <TableHead className="w-[300px]">Ingredient Name</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Risk Level</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading && ingredients === undefined ? (
                <TableRow>
                  <TableCell colSpan={4} className="h-40 text-center">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto text-primary mb-2" />
                    <span className="text-muted-foreground">Loading database...</span>
                  </TableCell>
                </TableRow>
              ) : isError ? (
                <TableRow>
                  <TableCell colSpan={4} className="h-40 text-center text-destructive">
                    Failed to load ingredients. Please try again.
                  </TableCell>
                </TableRow>
              ) : ingredients?.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="h-40 text-center text-muted-foreground">
                    No ingredients found matching your criteria.
                  </TableCell>
                </TableRow>
              ) : (
                ingredients?.map((ing) => (
                  <TableRow key={ing.id} className="hover:bg-muted/30 transition-colors">
                    <TableCell className="font-medium">
                      <div className="flex flex-col">
                        <span>{ing.name}</span>
                        {ing.code && <span className="text-xs text-muted-foreground">{ing.code}</span>}
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {ing.category || "Uncategorized"}
                    </TableCell>
                    <TableCell>
                      <Badge className={`${getRiskColor(ing.riskLevel)} capitalize font-semibold tracking-wide border-none`}>
                        {ing.riskLevel}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Link href={`/ingredient/${ing.id}`}>
                        <Button variant="ghost" size="sm" className="font-medium hover:text-primary">
                          View Details
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
        
        {ingredients && ingredients.length > 0 && (
          <div className="p-4 border-t flex items-center justify-between bg-muted/20">
            <span className="text-sm text-muted-foreground">
              Showing page {page}
            </span>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                Previous
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => setPage(p => p + 1)}
                disabled={ingredients.length < limit}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
