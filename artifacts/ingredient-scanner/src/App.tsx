import { Switch, Route, Router as WouterRouter } from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ScanProvider } from "./context/ScanContext";
import { Layout } from "./components/Layout";
import NotFound from "@/pages/not-found";

import Home from "./pages/Home";
import Results from "./pages/Results";
import Database from "./pages/Database";
import History from "./pages/History";
import Dashboard from "./pages/Dashboard";
import IngredientDetail from "./pages/IngredientDetail";

const queryClient = new QueryClient();

function Router() {
  return (
    <Layout>
      <Switch>
        <Route path="/" component={Home} />
        <Route path="/results" component={Results} />
        <Route path="/database" component={Database} />
        <Route path="/history" component={History} />
        <Route path="/dashboard" component={Dashboard} />
        <Route path="/ingredient/:id" component={IngredientDetail} />
        <Route component={NotFound} />
      </Switch>
    </Layout>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <ScanProvider>
          <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
            <Router />
          </WouterRouter>
        </ScanProvider>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
