"use client";

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  Cell,
  LineChart,
  Line,
  PieChart,
  Pie,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  AlertTriangle,
  RefreshCw,
  Clock,
  BarChart3,
  PieChart as PieChartIcon,
  Zap,
} from "lucide-react";

// --- Enhanced Type Definitions ---
interface CorrelationData {
  correlation_matrix: Record<string, Record<string, number>>;
  strongest_correlations: Array<{
    pair: string;
    correlation: number;
  }>;
  weakest_correlations: Array<{
    pair: string;
    correlation: number;
  }>;
  analysis_period: string;
  data_points?: number;
  coins_analyzed?: number;
}

interface VolatilityData {
  coin_id: string;
  volatility_score: number;
  daily_volatility: number;
  weekly_volatility: number;
  monthly_volatility: number;
  risk_level: string;
  trading_days?: number;
  min_daily_range?: number;
  max_daily_range?: number;
}

interface MarketSummary {
  total_market_cap: number;
  total_volume_24h: number;
  fear_greed_index?: number;
  trending_coins: string[];
  top_gainers: Array<{
    coin_id: string;
    change_24h: number;
  }>;
  top_losers: Array<{
    coin_id: string;
    change_24h: number;
  }>;
  total_coins_tracked?: number;
  average_change_24h?: number;
  last_updated?: string;
}

export default function AdvancedAnalysisPage() {
  const [correlationData, setCorrelationData] =
    useState<CorrelationData | null>(null);
  const [volatilityData, setVolatilityData] = useState<VolatilityData[]>([]);
  const [marketSummary, setMarketSummary] = useState<MarketSummary | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState("30");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true); // Enable by default
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(
    null
  );

  // Fetch data from enhanced backend APIs
  const fetchAdvancedData = async (showLoading = true) => {
    if (showLoading) setIsLoading(true);
    setError(null);

    try {
      const [corrResponse, volResponse, marketResponse] = await Promise.all([
        fetch(
          `http://localhost:8000/api/analysis/correlation?days=${selectedPeriod}`
        ),
        fetch(
          `http://localhost:8000/api/analysis/volatility?days=${selectedPeriod}`
        ),
        fetch(`http://localhost:8000/api/analysis/market-summary`),
      ]);

      if (corrResponse.ok) {
        const corrData = await corrResponse.json();
        setCorrelationData(corrData);
      }

      if (volResponse.ok) {
        const volData = await volResponse.json();
        // Extract volatility_data array from the response
        if (volData.volatility_data && Array.isArray(volData.volatility_data)) {
          setVolatilityData(volData.volatility_data);
        } else {
          setVolatilityData([]);
        }
      }

      if (marketResponse.ok) {
        const marketData = await marketResponse.json();
        setMarketSummary(marketData);
      }

      setLastUpdated(new Date());
    } catch (e: any) {
      setError(e.message);
    } finally {
      if (showLoading) setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAdvancedData();
  }, [selectedPeriod]);

  // Auto-refresh functionality
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        fetchAdvancedData(false);
      }, 30000); // Refresh every 30 seconds
      setRefreshInterval(interval);
    } else {
      if (refreshInterval) {
        clearInterval(refreshInterval);
        setRefreshInterval(null);
      }
    }

    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [autoRefresh]);

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel?.toLowerCase()) {
      case "low":
        return "bg-green-100 text-green-800 border-green-200";
      case "medium":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "high":
        return "bg-red-100 text-red-800 border-red-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const formatCorrelation = (value: number) => {
    return (value * 100).toFixed(1) + "%";
  };

  const formatVolatility = (value: number) => {
    return (value * 100).toFixed(2) + "%";
  };

  const formatCurrency = (value: number) => {
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value.toLocaleString()}`;
  };

  const getFearGreedColor = (index?: number) => {
    if (!index) return "bg-gray-100";
    if (index <= 25) return "bg-red-500";
    if (index <= 45) return "bg-orange-500";
    if (index <= 55) return "bg-yellow-500";
    if (index <= 75) return "bg-green-400";
    return "bg-green-600";
  };

  const getFearGreedText = (index?: number) => {
    if (!index) return "Unknown";
    if (index <= 25) return "Extreme Fear";
    if (index <= 45) return "Fear";
    if (index <= 55) return "Neutral";
    if (index <= 75) return "Greed";
    return "Extreme Greed";
  };

  if (isLoading) {
    return (
      <div className="p-4 md:p-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-500" />
            <div className="text-slate-500">Loading advanced analytics...</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-8 space-y-6">
      {/* Enhanced Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">
            Advanced Analytics
          </h1>
          <p className="text-slate-600">
            Real-time market analysis with multi-source data correlation
          </p>
          {lastUpdated && (
            <div className="flex items-center gap-2 mt-2 text-sm text-slate-500">
              <Clock className="h-4 w-4" />
              Last updated: {lastUpdated.toLocaleTimeString()}
              {autoRefresh && (
                <Badge
                  variant="outline"
                  className="ml-2 text-green-600 border-green-600"
                >
                  Auto-updating every 30s
                </Badge>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant={autoRefresh ? "default" : "outline"}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className="flex items-center gap-2"
          >
            <Zap className="h-4 w-4" />
            {autoRefresh ? "Auto-Refresh ON" : "Auto-Refresh OFF"}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchAdvancedData()}
            className="flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>

          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Analysis Period" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">Last 7 Days</SelectItem>
              <SelectItem value="30">Last 30 Days</SelectItem>
              <SelectItem value="90">Last 90 Days</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-6">
            <div className="text-red-700 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              Error loading data: {error}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Enhanced Market Summary Cards */}
      {marketSummary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="border-blue-200 bg-gradient-to-br from-blue-50 to-blue-100">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-blue-700">
                    Total Market Cap
                  </p>
                  <p className="text-2xl font-bold text-blue-900">
                    {formatCurrency(marketSummary.total_market_cap)}
                  </p>
                  {marketSummary.average_change_24h !== undefined && (
                    <p
                      className={`text-sm mt-1 flex items-center gap-1 ${
                        marketSummary.average_change_24h >= 0
                          ? "text-green-600"
                          : "text-red-600"
                      }`}
                    >
                      {marketSummary.average_change_24h >= 0 ? (
                        <TrendingUp className="h-3 w-3" />
                      ) : (
                        <TrendingDown className="h-3 w-3" />
                      )}
                      {marketSummary.average_change_24h.toFixed(2)}% avg
                    </p>
                  )}
                </div>
                <DollarSign className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-green-200 bg-gradient-to-br from-green-50 to-green-100">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-green-700">
                    24h Volume
                  </p>
                  <p className="text-2xl font-bold text-green-900">
                    {formatCurrency(marketSummary.total_volume_24h)}
                  </p>
                  <p className="text-sm text-green-600 mt-1">
                    {marketSummary.total_coins_tracked || 50} coins tracked
                  </p>
                </div>
                <Activity className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          {marketSummary.fear_greed_index !== undefined && (
            <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-purple-100">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-purple-700">
                      Fear & Greed Index
                    </p>
                    <p className="text-2xl font-bold text-purple-900">
                      {marketSummary.fear_greed_index}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${getFearGreedColor(
                            marketSummary.fear_greed_index
                          )}`}
                          style={{
                            width: `${marketSummary.fear_greed_index}%`,
                          }}
                        />
                      </div>
                    </div>
                    <p className="text-xs text-purple-600 mt-1">
                      {getFearGreedText(marketSummary.fear_greed_index)}
                    </p>
                  </div>
                  <BarChart3 className="h-8 w-8 text-purple-600" />
                </div>
              </CardContent>
            </Card>
          )}

          <Card className="border-orange-200 bg-gradient-to-br from-orange-50 to-orange-100">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-orange-700">
                    Top Performers
                  </p>
                  <div className="space-y-1 mt-2">
                    {marketSummary.top_gainers
                      ?.slice(0, 2)
                      .map((gainer, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between"
                        >
                          <span className="text-sm font-medium text-orange-900 capitalize">
                            {gainer.coin_id.replace("-", " ")}
                          </span>
                          <span className="text-sm font-bold text-green-600">
                            +{gainer.change_24h.toFixed(1)}%
                          </span>
                        </div>
                      ))}
                  </div>
                  <p className="text-xs text-orange-600 mt-2">24h gainers</p>
                </div>
                <TrendingUp className="h-8 w-8 text-orange-600" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Analysis Tabs */}
      <Tabs defaultValue="correlation" className="space-y-4">
        <TabsList>
          <TabsTrigger value="correlation">Correlation Analysis</TabsTrigger>
          <TabsTrigger value="volatility">Volatility Analysis</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        {/* Correlation Analysis Tab */}
        <TabsContent value="correlation" className="space-y-4">
          {correlationData ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Strongest Correlations */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">
                    Strongest Correlations
                  </CardTitle>
                  <CardDescription>
                    Cryptocurrencies with highest price correlation over{" "}
                    {selectedPeriod} days
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {correlationData.strongest_correlations
                      ?.slice(0, 5)
                      .map((item, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-3 bg-slate-50 rounded"
                        >
                          <span className="font-medium">{item.pair}</span>
                          <Badge
                            variant="secondary"
                            className="bg-green-100 text-green-800"
                          >
                            {formatCorrelation(item.correlation)}
                          </Badge>
                        </div>
                      ))}
                  </div>
                </CardContent>
              </Card>

              {/* Weakest Correlations */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">
                    Weakest Correlations
                  </CardTitle>
                  <CardDescription>
                    Cryptocurrencies with lowest price correlation
                    (diversification opportunities)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {correlationData.weakest_correlations
                      ?.slice(0, 5)
                      .map((item, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-3 bg-slate-50 rounded"
                        >
                          <span className="font-medium">{item.pair}</span>
                          <Badge
                            variant="secondary"
                            className="bg-blue-100 text-blue-800"
                          >
                            {formatCorrelation(item.correlation)}
                          </Badge>
                        </div>
                      ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="p-6 text-center text-slate-500">
                No correlation data available. The advanced analysis system may
                need to collect more data.
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Volatility Analysis Tab */}
        <TabsContent value="volatility" className="space-y-4">
          {volatilityData.length > 0 ? (
            <>
              {/* Data Freshness Indicator */}
              <Card className="border-green-200 bg-green-50">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2 text-green-700">
                      <Activity className="h-4 w-4" />
                      <span>
                        Live volatility data available for {selectedPeriod} day
                        analysis
                      </span>
                    </div>
                    <Badge
                      variant="outline"
                      className="text-green-600 border-green-600"
                    >
                      Real-time data
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Volatility Chart */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">
                      Volatility Comparison
                    </CardTitle>
                    <CardDescription>
                      Daily volatility scores across tracked cryptocurrencies
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div style={{ width: "100%", height: 300 }}>
                      <ResponsiveContainer>
                        <BarChart data={volatilityData.slice(0, 10)}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="coin_id" fontSize={10} />
                          <YAxis
                            tickFormatter={formatVolatility}
                            fontSize={12}
                          />
                          <Tooltip
                            formatter={(value: number) => [
                              formatVolatility(value),
                              "Volatility",
                            ]}
                          />
                          <Bar dataKey="daily_volatility" fill="#8884d8" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                {/* Risk Levels */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Risk Assessment</CardTitle>
                    <CardDescription>
                      Cryptocurrency risk levels based on volatility analysis
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3 max-h-80 overflow-y-auto">
                      {volatilityData.slice(0, 15).map((item, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-3 bg-slate-50 rounded"
                        >
                          <div>
                            <span className="font-medium capitalize">
                              {item.coin_id}
                            </span>
                            <p className="text-sm text-slate-600">
                              {formatVolatility(item.daily_volatility)} daily
                              vol
                            </p>
                          </div>
                          <Badge className={getRiskColor(item.risk_level)}>
                            {item.risk_level}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </>
          ) : (
            <Card>
              <CardContent className="p-6 text-center text-slate-500">
                No volatility data available. The advanced analysis system may
                need to collect more data.
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-4">
          {marketSummary && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Top Gainers */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-green-500" />
                    Top Gainers (24h)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {marketSummary.top_gainers
                      ?.slice(0, 8)
                      .map((item, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-3 bg-green-50 rounded"
                        >
                          <span className="font-medium capitalize">
                            {item.coin_id}
                          </span>
                          <Badge className="bg-green-100 text-green-800">
                            +{item.change_24h.toFixed(2)}%
                          </Badge>
                        </div>
                      ))}
                  </div>
                </CardContent>
              </Card>

              {/* Top Losers */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <TrendingDown className="h-5 w-5 text-red-500" />
                    Top Losers (24h)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {marketSummary.top_losers
                      ?.slice(0, 8)
                      .map((item, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-3 bg-red-50 rounded"
                        >
                          <span className="font-medium capitalize">
                            {item.coin_id}
                          </span>
                          <Badge className="bg-red-100 text-red-800">
                            {item.change_24h.toFixed(2)}%
                          </Badge>
                        </div>
                      ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
