import React from "react";
import { 
  useGetStatsSummary,
  useGetRiskDistribution,
  useGetTopRiskyIngredients,
  useGetCategoryBreakdown,
  getGetStatsSummaryQueryKey,
  getGetRiskDistributionQueryKey,
  getGetTopRiskyIngredientsQueryKey,
  getGetCategoryBreakdownQueryKey
} from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Legend } from "recharts";
import { Loader2, Database, Activity, AlertTriangle, ShieldAlert } from "lucide-react";

export default function Dashboard() {
  const { data: summary, isLoading: loadingSummary } = useGetStatsSummary({
    query: { queryKey: getGetStatsSummaryQueryKey() }
  });
  
  const { data: riskDist, isLoading: loadingDist } = useGetRiskDistribution({
    query: { queryKey: getGetRiskDistributionQueryKey() }
  });
  
  const { data: topRisky, isLoading: loadingTop } = useGetTopRiskyIngredients({ limit: 10 }, {
    query: { queryKey: getGetTopRiskyIngredientsQueryKey({ limit: 10 }) }
  });
  
  const { data: categories, isLoading: loadingCat } = useGetCategoryBreakdown({
    query: { queryKey: getGetCategoryBreakdownQueryKey() }
  });

  const isLoading = loadingSummary || loadingDist || loadingTop || loadingCat;

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] space-y-4">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <p className="text-muted-foreground">Loading dashboard data...</p>
      </div>
    );
  }

  const pieData = riskDist ? [
    { name: 'Low Risk', value: riskDist.low, color: 'hsl(var(--risk-low))' },
    { name: 'Medium Risk', value: riskDist.medium, color: 'hsl(var(--risk-medium))' },
    { name: 'High Risk', value: riskDist.high, color: 'hsl(var(--risk-high))' },
    { name: 'Unknown', value: riskDist.unknown, color: 'hsl(var(--risk-unknown))' },
  ].filter(d => d.value > 0) : [];

  return (
    <div className="space-y-6 animate-in fade-in duration-500 pb-10">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">Platform Insights</h1>
        <p className="text-muted-foreground">Aggregated data across all ingredients and scans.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Ingredients</CardTitle>
            <Database className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{summary?.totalIngredients.toLocaleString() || 0}</div>
          </CardContent>
        </Card>
        
        <Card className="shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Analyses Performed</CardTitle>
            <Activity className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{summary?.totalScans.toLocaleString() || 0}</div>
          </CardContent>
        </Card>
        
        <Card className="shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">High Risk Substances</CardTitle>
            <AlertTriangle className="w-4 h-4 text-risk-high" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-risk-high">{summary?.highRiskCount.toLocaleString() || 0}</div>
          </CardContent>
        </Card>
        
        <Card className="shadow-sm">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Avg Risk Score</CardTitle>
            <ShieldAlert className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{Math.round(summary?.avgRiskScore || 0)}/100</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle>Global Risk Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                    stroke="none"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip 
                    formatter={(value: number) => [`${value} ingredients`, 'Count']}
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                  />
                  <Legend verticalAlign="bottom" height={36} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardHeader>
            <CardTitle>Top Ingredient Categories</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={categories?.slice(0, 7) || []}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="hsl(var(--border))" />
                  <XAxis type="number" tick={{fill: 'hsl(var(--muted-foreground))'}} axisLine={false} tickLine={false} />
                  <YAxis dataKey="category" type="category" width={120} tick={{fill: 'hsl(var(--foreground))', fontSize: 12}} axisLine={false} tickLine={false} />
                  <RechartsTooltip 
                    cursor={{fill: 'hsl(var(--muted)/0.5)'}}
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                  />
                  <Bar dataKey="count" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} barSize={24} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-sm lg:col-span-2">
          <CardHeader>
            <CardTitle>Most Frequently Flagged Risky Ingredients</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[350px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={topRisky || []}
                  margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                >
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                  <XAxis 
                    dataKey="name" 
                    angle={-45} 
                    textAnchor="end" 
                    height={80} 
                    tick={{fill: 'hsl(var(--foreground))', fontSize: 11}} 
                    interval={0}
                    axisLine={false} 
                    tickLine={false}
                  />
                  <YAxis tick={{fill: 'hsl(var(--muted-foreground))'}} axisLine={false} tickLine={false} />
                  <RechartsTooltip 
                    cursor={{fill: 'hsl(var(--muted)/0.5)'}}
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                  />
                  <Bar dataKey="count" fill="hsl(var(--risk-high))" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
