"use client";

import { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  Area,
  AreaChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ComposedChart,
  ReferenceLine,
  Brush,
} from "recharts";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  SlidersHorizontal,
  Search,
  TrendingUp,
  BarChart3,
  Settings,
  Filter,
  X,
  Menu,
  ChevronDown,
  ChevronUp,
  Bitcoin,
  Coins,
  CheckCircle,
  Circle,
  Wifi,
  WifiOff,
} from "lucide-react";
import { ChartSkeleton, PageSkeleton } from "@/components/ui/skeleton";
import {
  useSimpleCoinWebSocket,
  SimpleWebSocketStatus,
} from "@/hooks/useSimpleWebSocket";
import { getCachedPrices, getCachedCoinList } from "@/lib/cache";

// --- Enhanced Type Definitions for ALL Available Indicators ---
type IndicatorVisibility = {
  sma_20: boolean;
  sma_100: boolean;
  sma_200: boolean;
  ema_12: boolean;
  ema_26: boolean;
  ema_50: boolean;
  rsi_14: boolean;
  macd_line: boolean;
  macd_signal: boolean;
  macd_hist: boolean;
  bollinger_bands: boolean;
  stochrsi_k: boolean;
  stochrsi_d: boolean;
  williams_r_14: boolean;
  cci_20: boolean;
  atr_14: boolean;
  psar_long: boolean;
  psar_short: boolean;
};
type IndicatorId = keyof IndicatorVisibility;

interface PriceData {
  timestamp: string;
  price_usd: number;
  market_cap?: number;
  volume_24h?: number;
  change_24h?: number;
  sma_20?: number;
  sma_100?: number;
  sma_200?: number;
  ema_12?: number;
  ema_26?: number;
  ema_50?: number;
  rsi_14?: number;
  macd_line?: number;
  macd_signal?: number;
  macd_hist?: number;
  bb_lower?: number;
  bb_mid?: number;
  bb_upper?: number;
  stochrsi_k?: number;
  stochrsi_d?: number;
  williams_r_14?: number;
  cci_20?: number;
  atr_14?: number;
  psar_long?: number;
  psar_short?: number;
}

// --- Enhanced Indicator Configurations ---
const movingAverageIndicators: {
  id: IndicatorId;
  name: string;
  color: string;
}[] = [
  { id: "sma_20", name: "SMA (20)", color: "#82ca9d" },
  { id: "sma_100", name: "SMA (100)", color: "#8dd1e1" },
  { id: "sma_200", name: "SMA (200)", color: "#7dd3c0" },
  { id: "ema_12", name: "EMA (12)", color: "#ffc658" },
  { id: "ema_26", name: "EMA (26)", color: "#ffb347" },
  { id: "ema_50", name: "EMA (50)", color: "#ff9f40" },
];

const trendIndicators: { id: IndicatorId; name: string; color: string }[] = [
  { id: "bollinger_bands", name: "Bollinger Bands", color: "#8884d8" },
  { id: "psar_long", name: "PSAR Long", color: "#9c88ff" },
  { id: "psar_short", name: "PSAR Short", color: "#ff6b9d" },
];

const macdIndicators: { id: IndicatorId; name: string; color: string }[] = [
  { id: "macd_line", name: "MACD Line", color: "#ff8042" },
  { id: "macd_signal", name: "MACD Signal", color: "#0088fe" },
  { id: "macd_hist", name: "MACD Histogram", color: "#00c49f" },
];

const oscillatorIndicators: { id: IndicatorId; name: string; color: string }[] =
  [
    { id: "rsi_14", name: "RSI (14)", color: "#ff8042" },
    { id: "stochrsi_k", name: "Stoch RSI %K", color: "#8884d8" },
    { id: "stochrsi_d", name: "Stoch RSI %D", color: "#82ca9d" },
    { id: "williams_r_14", name: "Williams %R", color: "#ffc658" },
    { id: "cci_20", name: "CCI (20)", color: "#ff7300" },
  ];

const momentumIndicators: { id: IndicatorId; name: string; color: string }[] = [
  { id: "atr_14", name: "ATR (14)", color: "#f8b500" },
];

// --- Custom Tooltip Component ---
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="p-2 bg-white/80 backdrop-blur-sm border border-slate-200 rounded-lg shadow-lg">
        <p className="label font-bold text-slate-700">{`${label}`}</p>
        {payload.map((pld: any) => (
          <p
            key={pld.dataKey}
            style={{ color: pld.stroke || pld.fill }}
            className="intro text-sm"
          >
            {`${pld.name}: ${
              pld.dataKey.startsWith("rsi")
                ? pld.value.toFixed(2)
                : "$" +
                  pld.value.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })
            }`}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// --- NEW HELPER FUNCTIONS for better formatting ---
const formatTimestamp = (timestamp: string, timeframe: string) => {
  const date = new Date(timestamp);
  try {
    switch (timeframe) {
      case "24h":
        return date.toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        });
      case "7d":
      case "30d":
        return date.toLocaleDateString([], { month: "short", day: "numeric" });
      default: // 'all'
        return date.toLocaleDateString([], { year: "2-digit", month: "short" });
    }
  } catch (error) {
    return timestamp; // Fallback to original string if formatting fails
  }
};

const formatYAxisTick = (value: number) => {
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(1)}k`; // e.g., $115.5k
  }
  if (value >= 1) {
    return `$${value.toFixed(0)}`; // e.g., $18
  }
  return `$${value.toFixed(3)}`; // e.g., $0.123
};

// --- Main Page Component ---
export default function AnalysisPage() {
  const [prices, setPrices] = useState<PriceData[]>([]);
  const [visibleIndicators, setVisibleIndicators] =
    useState<IndicatorVisibility>({
      sma_20: true,
      sma_100: false,
      sma_200: false,
      ema_12: false,
      ema_26: false,
      ema_50: false,
      rsi_14: false,
      macd_line: false,
      macd_signal: false,
      macd_hist: false,
      bollinger_bands: false,
      stochrsi_k: false,
      stochrsi_d: false,
      williams_r_14: false,
      cci_20: false,
      atr_14: false,
      psar_long: false,
      psar_short: false,
    });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [availableCoins, setAvailableCoins] = useState<string[]>([]);
  const [selectedCoin, setSelectedCoin] = useState<string>("bitcoin");
  const [timeframe, setTimeframe] = useState("7d");
  const [scale, setScale] = useState<"linear" | "log">("linear");
  const [chartType, setChartType] = useState<"line" | "area" | "candlestick">(
    "line"
  );
  const [showVolume, setShowVolume] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
  const [expandedSections, setExpandedSections] = useState({
    movingAverages: true,
    trendAnalysis: false,
    macdFamily: false,
    oscillators: false,
    momentum: false,
  });
  const [useRealTime, setUseRealTime] = useState(false); // FIXED: Disabled by default

  // WebSocket connection for real-time updates - RESTORED for testing
  const {
    priceData: realtimePriceData,
    isConnected,
    error: wsError,
    reconnectAttempts,
  } = useSimpleCoinWebSocket(selectedCoin, useRealTime);

  // Mock WebSocket data for testing - will show "Connecting..."

  // Filter coins based on search term
  const filteredCoins = availableCoins.filter((coin) =>
    coin.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Get coin icon based on coin name - Comprehensive cryptocurrency support
  const getCoinIcon = (coinName: string) => {
    const iconMap: Record<string, React.ReactElement> = {
      // Major Cryptocurrencies
      bitcoin: <Bitcoin className="h-4 w-4 text-orange-500" />,
      ethereum: (
        <div className="h-4 w-4 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
          Ξ
        </div>
      ),

      // Top Altcoins
      "binance-coin": (
        <div className="h-4 w-4 bg-yellow-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
          B
        </div>
      ),
      cardano: (
        <div className="h-4 w-4 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
          ₳
        </div>
      ),
      solana: (
        <div className="h-4 w-4 bg-purple-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
          ◎
        </div>
      ),
      xrp: (
        <div className="h-4 w-4 bg-blue-400 rounded-full flex items-center justify-center text-white text-xs font-bold">
          X
        </div>
      ),
      dogecoin: (
        <div className="h-4 w-4 bg-yellow-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
          Ð
        </div>
      ),
      avalanche: (
        <div className="h-4 w-4 bg-red-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
          △
        </div>
      ),
      polygon: (
        <div className="h-4 w-4 bg-purple-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
          ⬟
        </div>
      ),
      chainlink: (
        <div className="h-4 w-4 bg-blue-400 rounded-full flex items-center justify-center text-white text-xs font-bold">
          ⬡
        </div>
      ),
      polkadot: (
        <div className="h-4 w-4 bg-pink-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
          ●
        </div>
      ),

      // DeFi Tokens
      uniswap: (
        <div className="h-4 w-4 bg-pink-400 rounded-full flex items-center justify-center text-white text-xs font-bold">
          🦄
        </div>
      ),
      compound: (
        <div className="h-4 w-4 bg-green-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
          C
        </div>
      ),
      aave: (
        <div className="h-4 w-4 bg-purple-400 rounded-full flex items-center justify-center text-white text-xs font-bold">
          A
        </div>
      ),
      maker: (
        <div className="h-4 w-4 bg-teal-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
          M
        </div>
      ),

      // Layer 2 & Scaling
      arbitrum: (
        <div className="h-4 w-4 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
          ▲
        </div>
      ),
      optimism: (
        <div className="h-4 w-4 bg-red-400 rounded-full flex items-center justify-center text-white text-xs font-bold">
          O
        </div>
      ),

      // Smart Contract Platforms
      cosmos: (
        <div className="h-4 w-4 bg-purple-700 rounded-full flex items-center justify-center text-white text-xs font-bold">
          ⚛
        </div>
      ),
      algorand: (
        <div className="h-4 w-4 bg-black rounded-full flex items-center justify-center text-white text-xs font-bold">
          A
        </div>
      ),
      near: (
        <div className="h-4 w-4 bg-gray-700 rounded-full flex items-center justify-center text-white text-xs font-bold">
          N
        </div>
      ),

      // Meme Coins
      "shiba-inu": (
        <div className="h-4 w-4 bg-orange-400 rounded-full flex items-center justify-center text-white text-xs font-bold">
          🐕
        </div>
      ),
      pepe: (
        <div className="h-4 w-4 bg-green-400 rounded-full flex items-center justify-center text-white text-xs font-bold">
          🐸
        </div>
      ),

      // Stablecoins
      tether: (
        <div className="h-4 w-4 bg-green-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
          ₮
        </div>
      ),
      "usd-coin": (
        <div className="h-4 w-4 bg-blue-700 rounded-full flex items-center justify-center text-white text-xs font-bold">
          $
        </div>
      ),

      // Exchange Tokens
      "crypto-com-coin": (
        <div className="h-4 w-4 bg-blue-800 rounded-full flex items-center justify-center text-white text-xs font-bold">
          C
        </div>
      ),
      okb: (
        <div className="h-4 w-4 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
          O
        </div>
      ),

      // Additional Popular Coins
      litecoin: (
        <div className="h-4 w-4 bg-gray-400 rounded-full flex items-center justify-center text-white text-xs font-bold">
          Ł
        </div>
      ),
      "bitcoin-cash": (
        <div className="h-4 w-4 bg-green-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
          ₿
        </div>
      ),
      stellar: (
        <div className="h-4 w-4 bg-blue-300 rounded-full flex items-center justify-center text-white text-xs font-bold">
          ✦
        </div>
      ),
      "terra-luna": (
        <div className="h-4 w-4 bg-yellow-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
          ☽
        </div>
      ),
      monero: (
        <div className="h-4 w-4 bg-orange-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
          ɱ
        </div>
      ),
      "ethereum-classic": (
        <div className="h-4 w-4 bg-green-700 rounded-full flex items-center justify-center text-white text-xs font-bold">
          Ξ
        </div>
      ),
      eos: (
        <div className="h-4 w-4 bg-gray-800 rounded-full flex items-center justify-center text-white text-xs font-bold">
          E
        </div>
      ),
      tron: (
        <div className="h-4 w-4 bg-red-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
          T
        </div>
      ),
      iota: (
        <div className="h-4 w-4 bg-gray-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
          ι
        </div>
      ),
      vechain: (
        <div className="h-4 w-4 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
          V
        </div>
      ),
      filecoin: (
        <div className="h-4 w-4 bg-blue-400 rounded-full flex items-center justify-center text-white text-xs font-bold">
          ⨎
        </div>
      ),
      "the-graph": (
        <div className="h-4 w-4 bg-purple-500 rounded-full flex items-center justify-center text-white text-xs font-bold">
          G
        </div>
      ),
      hedera: (
        <div className="h-4 w-4 bg-gray-700 rounded-full flex items-center justify-center text-white text-xs font-bold">
          ℏ
        </div>
      ),
      theta: (
        <div className="h-4 w-4 bg-teal-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
          Θ
        </div>
      ),
    };

    // Try exact match first, then fallback to generic coin icon with enhanced pattern matching
    const key = coinName.toLowerCase().replace(/\s+/g, "-");

    // Enhanced fallback system: try multiple naming patterns including ticker symbols
    const tryPatterns = [
      coinName.toLowerCase(), // exact lowercase
      key, // with dashes
      coinName.toLowerCase().replace(/[-_\s]/g, ""), // no separators
      coinName.toUpperCase(), // uppercase ticker
      coinName.toLowerCase().split("-")[0], // first part of hyphenated names
      coinName.toLowerCase().split(" ")[0], // first word
      // Common ticker mappings
      coinName === "btc" ? "bitcoin" : null,
      coinName === "eth" ? "ethereum" : null,
      coinName === "bnb" ? "binance-coin" : null,
      coinName === "ada" ? "cardano" : null,
      coinName === "sol" ? "solana" : null,
      coinName === "dot" ? "polkadot" : null,
      coinName === "matic" ? "polygon" : null,
      coinName === "link" ? "chainlink" : null,
      coinName === "avax" ? "avalanche" : null,
      coinName === "trx" ? "tron" : null,
      coinName === "usdt" ? "tether" : null,
      coinName === "usdc" ? "usd-coin" : null,
      coinName === "uni" ? "uniswap" : null,
      coinName === "ltc" ? "litecoin" : null,
      coinName === "bch" ? "bitcoin-cash" : null,
      coinName === "xlm" ? "stellar" : null,
      coinName === "xmr" ? "monero" : null,
      coinName === "etc" ? "ethereum-classic" : null,
      coinName === "atom" ? "cosmos" : null,
      coinName === "algo" ? "algorand" : null,
      coinName === "shib" ? "shiba-inu" : null,
      coinName === "cro" ? "crypto-com-coin" : null,
      coinName === "grt" ? "the-graph" : null,
      coinName === "hbar" ? "hedera" : null,
      coinName === "vet" ? "vechain" : null,
      coinName === "fil" ? "filecoin" : null,
      coinName === "comp" ? "compound" : null,
      coinName === "mkr" ? "maker" : null,
      coinName === "arb" ? "arbitrum" : null,
      coinName === "op" ? "optimism" : null,
    ].filter(Boolean);

    for (const pattern of tryPatterns) {
      if (pattern && iconMap[pattern]) {
        return iconMap[pattern];
      }
    }

    // Enhanced fallback with gradient styling and better visual appeal
    return (
      <div className="h-4 w-4 bg-gradient-to-br from-gray-400 to-gray-600 rounded-full flex items-center justify-center text-white">
        <Coins className="h-3 w-3" />
      </div>
    );
  };

  // Toggle section expansion
  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  // Handle search input with suggestions
  const handleSearchChange = (value: string) => {
    setSearchTerm(value);
    setShowSuggestions(value.length > 0);
    setSelectedSuggestionIndex(-1);
  };

  // Handle keyboard navigation in suggestions
  const handleSearchKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions || filteredCoins.length === 0) return;

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setSelectedSuggestionIndex((prev) =>
          prev < filteredCoins.length - 1 ? prev + 1 : 0
        );
        break;
      case "ArrowUp":
        e.preventDefault();
        setSelectedSuggestionIndex((prev) =>
          prev > 0 ? prev - 1 : filteredCoins.length - 1
        );
        break;
      case "Enter":
        e.preventDefault();
        if (selectedSuggestionIndex >= 0) {
          setSelectedCoin(filteredCoins[selectedSuggestionIndex]);
          setSearchTerm("");
          setShowSuggestions(false);
        }
        break;
      case "Escape":
        setShowSuggestions(false);
        setSelectedSuggestionIndex(-1);
        break;
    }
  };

  // Select coin from suggestions
  const selectCoinFromSuggestion = (coin: string) => {
    setSelectedCoin(coin);
    setSearchTerm("");
    setShowSuggestions(false);
  };

  useEffect(() => {
    const fetchCoins = async () => {
      try {
        const data = await getCachedCoinList();
        if (data.coins && data.coins.length > 0) {
          setAvailableCoins(data.coins);
          if (!data.coins.includes("bitcoin")) {
            setSelectedCoin(data.coins[0]);
          }
        }
      } catch (e: any) {
        console.error("Failed to fetch coins:", e);
        setAvailableCoins(["bitcoin", "ethereum"]);
      }
    };
    fetchCoins();
  }, []);

  useEffect(() => {
    if (!selectedCoin) return;
    const fetchPrices = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const priceData = await getCachedPrices(selectedCoin, timeframe);
        console.log(
          "Data received by Frontend Component:",
          priceData.prices.slice(0, 5)
        );
        const formattedPriceData = priceData.prices.map((p: any) => ({
          ...p,
          timestamp: formatTimestamp(p.timestamp, timeframe),
        }));
        setPrices(formattedPriceData);
      } catch (e: any) {
        setError(e.message);
        setPrices([]);
      } finally {
        setIsLoading(false);
      }
    };

    // Only fetch historical data if not using real-time or if timeframe changed
    if (!useRealTime || timeframe !== "24h") {
      fetchPrices();
    } else {
      setIsLoading(false);
    }
  }, [selectedCoin, timeframe, useRealTime]);

  // Update prices with real-time data when available
  useEffect(() => {
    if (useRealTime && realtimePriceData && timeframe === "24h") {
      const formattedData = {
        ...realtimePriceData,
        timestamp: formatTimestamp(realtimePriceData.timestamp, timeframe),
      };

      setPrices((prevPrices) => {
        const updated = [...prevPrices];
        // Add new data point or update the latest one
        if (
          updated.length === 0 ||
          updated[updated.length - 1].timestamp !== formattedData.timestamp
        ) {
          updated.push(formattedData);
          // Keep only last 100 data points for performance
          return updated.slice(-100);
        } else {
          updated[updated.length - 1] = formattedData;
          return updated;
        }
      });
    }
  }, [realtimePriceData, useRealTime, timeframe]);

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest(".search-container")) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleIndicatorToggle = (id: IndicatorId) => {
    setVisibleIndicators((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  // Quick preset functions for better UX
  const applyPreset = (preset: string) => {
    let newIndicators: IndicatorVisibility;

    switch (preset) {
      case "basic":
        newIndicators = {
          ...Object.fromEntries(
            Object.keys(visibleIndicators).map((k) => [k, false])
          ),
          sma_20: true,
          ema_50: true,
          rsi_14: true,
        } as IndicatorVisibility;
        break;
      case "trend":
        newIndicators = {
          ...Object.fromEntries(
            Object.keys(visibleIndicators).map((k) => [k, false])
          ),
          sma_20: true,
          sma_100: true,
          ema_12: true,
          ema_26: true,
          bollinger_bands: true,
        } as IndicatorVisibility;
        break;
      case "momentum":
        newIndicators = {
          ...Object.fromEntries(
            Object.keys(visibleIndicators).map((k) => [k, false])
          ),
          rsi_14: true,
          macd_line: true,
          macd_signal: true,
          stochrsi_k: true,
          stochrsi_d: true,
        } as IndicatorVisibility;
        break;
      case "advanced":
        newIndicators = {
          ...Object.fromEntries(
            Object.keys(visibleIndicators).map((k) => [k, false])
          ),
          sma_20: true,
          ema_50: true,
          rsi_14: true,
          macd_line: true,
          bollinger_bands: true,
          williams_r_14: true,
          cci_20: true,
          atr_14: true,
        } as IndicatorVisibility;
        break;
      case "all":
        newIndicators = Object.fromEntries(
          Object.keys(visibleIndicators).map((k) => [k, true])
        ) as IndicatorVisibility;
        break;
      case "none":
      default:
        newIndicators = Object.fromEntries(
          Object.keys(visibleIndicators).map((k) => [k, false])
        ) as IndicatorVisibility;
        break;
    }

    setVisibleIndicators(newIndicators);
  };

  const getActiveIndicatorCount = () => {
    return Object.values(visibleIndicators).filter(Boolean).length;
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-80 bg-white shadow-xl transform transition-transform duration-300 ease-in-out ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } lg:relative lg:translate-x-0 lg:flex lg:flex-col`}
      >
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">
            Analysis Controls
          </h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Enhanced Coin Selection with Search */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-gray-700 flex items-center gap-2">
              <Coins className="h-4 w-4" />
              Select Cryptocurrency
            </h3>

            {/* Search with Autocomplete */}
            <div className="relative search-container">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search cryptocurrencies..."
                  value={searchTerm}
                  onChange={(e) => handleSearchChange(e.target.value)}
                  onKeyDown={handleSearchKeyDown}
                  onFocus={() => searchTerm && setShowSuggestions(true)}
                  className="pl-10 pr-4 py-2"
                />
              </div>

              {/* Autocomplete Suggestions */}
              {showSuggestions && filteredCoins.length > 0 && (
                <div className="absolute top-full left-0 right-0 z-50 mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto">
                  {filteredCoins.slice(0, 8).map((coin, index) => (
                    <div
                      key={coin}
                      className={`p-3 cursor-pointer hover:bg-gray-50 flex items-center gap-3 border-b last:border-b-0 ${
                        index === selectedSuggestionIndex
                          ? "bg-blue-50 border-blue-200"
                          : ""
                      }`}
                      onClick={() => selectCoinFromSuggestion(coin)}
                    >
                      {getCoinIcon(coin)}
                      <div className="flex-1">
                        <div className="font-medium text-sm capitalize text-gray-900">
                          {coin}
                        </div>
                        <div className="text-xs text-gray-500">
                          Click to select
                        </div>
                      </div>
                      {coin === selectedCoin && (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Enhanced Coin Select - Consistent Sizing */}
            <div className="bg-gray-50 rounded-lg p-3 border">
              <div className="text-xs text-gray-600 mb-2">
                Currently Selected:
              </div>
              <div className="flex items-center gap-3 p-2 bg-white rounded border h-10">
                {getCoinIcon(selectedCoin)}
                <div className="flex-1">
                  <div className="font-medium text-sm capitalize text-gray-900 leading-tight">
                    {selectedCoin}
                  </div>
                  <div className="text-xs text-gray-500 leading-tight">
                    Active cryptocurrency
                  </div>
                </div>
                <TrendingUp className="h-4 w-4 text-green-500" />
              </div>
            </div>

            {/* Primary: Enhanced Select Dropdown with Consistent Height */}
            <Select value={selectedCoin} onValueChange={setSelectedCoin}>
              <SelectTrigger className="h-10 w-full">
                <div className="flex items-center gap-3 w-full">
                  {getCoinIcon(selectedCoin)}
                  <div className="text-left flex-1">
                    <div className="font-medium capitalize text-sm leading-tight">
                      {selectedCoin}
                    </div>
                    <div className="text-xs text-gray-500 leading-tight">
                      Cryptocurrency
                    </div>
                  </div>
                </div>
              </SelectTrigger>
              <SelectContent className="max-h-60 w-full">
                {availableCoins.map((coin) => (
                  <SelectItem key={coin} value={coin} className="h-10">
                    <div className="flex items-center gap-3 w-full">
                      {getCoinIcon(coin)}
                      <div className="flex-1">
                        <div className="font-medium capitalize text-sm leading-tight">
                          {coin}
                        </div>
                        <div className="text-xs text-gray-500 leading-tight">
                          Select to analyze
                        </div>
                      </div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Timeframe Selection - Consistent Sizing */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-gray-700">Time Period</h3>
            <ToggleGroup
              type="single"
              value={timeframe}
              onValueChange={(value) => value && setTimeframe(value)}
              size="sm"
              className="grid grid-cols-2 gap-2 w-full"
            >
              <ToggleGroupItem
                value="24h"
                className="w-full h-10 flex items-center justify-center"
              >
                24h
              </ToggleGroupItem>
              <ToggleGroupItem
                value="7d"
                className="w-full h-10 flex items-center justify-center"
              >
                7d
              </ToggleGroupItem>
              <ToggleGroupItem
                value="30d"
                className="w-full h-10 flex items-center justify-center"
              >
                30d
              </ToggleGroupItem>
              <ToggleGroupItem
                value="all"
                className="w-full h-10 flex items-center justify-center"
              >
                All
              </ToggleGroupItem>
            </ToggleGroup>
          </div>

          {/* Quick Presets - Consistent Sizing */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-gray-700">Quick Presets</h3>
            <div className="grid grid-cols-2 gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => applyPreset("basic")}
                className="w-full h-10"
              >
                Basic
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => applyPreset("trend")}
                className="w-full h-10"
              >
                Trend
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => applyPreset("momentum")}
                className="w-full h-10"
              >
                Momentum
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => applyPreset("advanced")}
                className="w-full h-10"
              >
                Advanced
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => applyPreset("all")}
                className="w-full h-10 font-medium"
              >
                All
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => applyPreset("none")}
                className="w-full h-10"
              >
                None
              </Button>
            </div>
          </div>

          {/* Enhanced Technical Indicators with Collapsible Sections */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-700 flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Technical Indicators
              </h3>
              <div className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                {getActiveIndicatorCount()} active
              </div>
            </div>

            {/* Moving Averages Section */}
            <div className="border border-gray-200 rounded-lg">
              <button
                onClick={() => toggleSection("movingAverages")}
                className="w-full p-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm font-medium text-gray-700">
                    Moving Averages
                  </span>
                  <span className="text-xs text-gray-500">
                    (
                    {
                      movingAverageIndicators.filter(
                        (ind) => visibleIndicators[ind.id]
                      ).length
                    }
                    )
                  </span>
                </div>
                {expandedSections.movingAverages ? (
                  <ChevronUp className="h-4 w-4 text-gray-400" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-gray-400" />
                )}
              </button>
              {expandedSections.movingAverages && (
                <div className="px-3 pb-3 space-y-2 border-t border-gray-100">
                  {movingAverageIndicators.map((indicator) => (
                    <div
                      key={indicator.id}
                      className="flex items-center justify-between py-1"
                    >
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id={indicator.id}
                          checked={visibleIndicators[indicator.id]}
                          onCheckedChange={() =>
                            handleIndicatorToggle(indicator.id)
                          }
                        />
                        <Label
                          htmlFor={indicator.id}
                          className="text-xs cursor-pointer flex-1"
                          style={{ color: indicator.color }}
                        >
                          {indicator.name}
                        </Label>
                      </div>
                      <div
                        className="h-2 w-2 rounded-full"
                        style={{ backgroundColor: indicator.color }}
                      ></div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Trend Analysis Section */}
            <div className="border border-gray-200 rounded-lg">
              <button
                onClick={() => toggleSection("trendAnalysis")}
                className="w-full p-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 bg-blue-500 rounded-full"></div>
                  <span className="text-sm font-medium text-gray-700">
                    Trend Analysis
                  </span>
                  <span className="text-xs text-gray-500">
                    (
                    {
                      trendIndicators.filter((ind) => visibleIndicators[ind.id])
                        .length
                    }
                    )
                  </span>
                </div>
                {expandedSections.trendAnalysis ? (
                  <ChevronUp className="h-4 w-4 text-gray-400" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-gray-400" />
                )}
              </button>
              {expandedSections.trendAnalysis && (
                <div className="px-3 pb-3 space-y-2 border-t border-gray-100">
                  {trendIndicators.map((indicator) => (
                    <div
                      key={indicator.id}
                      className="flex items-center justify-between py-1"
                    >
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id={indicator.id}
                          checked={visibleIndicators[indicator.id]}
                          onCheckedChange={() =>
                            handleIndicatorToggle(indicator.id)
                          }
                        />
                        <Label
                          htmlFor={indicator.id}
                          className="text-xs cursor-pointer flex-1"
                          style={{ color: indicator.color }}
                        >
                          {indicator.name}
                        </Label>
                      </div>
                      <div
                        className="h-2 w-2 rounded-full"
                        style={{ backgroundColor: indicator.color }}
                      ></div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* MACD Family Section */}
            <div className="border border-gray-200 rounded-lg">
              <button
                onClick={() => toggleSection("macdFamily")}
                className="w-full p-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 bg-orange-500 rounded-full"></div>
                  <span className="text-sm font-medium text-gray-700">
                    MACD Family
                  </span>
                  <span className="text-xs text-gray-500">
                    (
                    {
                      macdIndicators.filter((ind) => visibleIndicators[ind.id])
                        .length
                    }
                    )
                  </span>
                </div>
                {expandedSections.macdFamily ? (
                  <ChevronUp className="h-4 w-4 text-gray-400" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-gray-400" />
                )}
              </button>
              {expandedSections.macdFamily && (
                <div className="px-3 pb-3 space-y-2 border-t border-gray-100">
                  {macdIndicators.map((indicator) => (
                    <div
                      key={indicator.id}
                      className="flex items-center justify-between py-1"
                    >
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id={indicator.id}
                          checked={visibleIndicators[indicator.id]}
                          onCheckedChange={() =>
                            handleIndicatorToggle(indicator.id)
                          }
                        />
                        <Label
                          htmlFor={indicator.id}
                          className="text-xs cursor-pointer flex-1"
                          style={{ color: indicator.color }}
                        >
                          {indicator.name}
                        </Label>
                      </div>
                      <div
                        className="h-2 w-2 rounded-full"
                        style={{ backgroundColor: indicator.color }}
                      ></div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Oscillators Section */}
            <div className="border border-gray-200 rounded-lg">
              <button
                onClick={() => toggleSection("oscillators")}
                className="w-full p-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 bg-purple-500 rounded-full"></div>
                  <span className="text-sm font-medium text-gray-700">
                    Oscillators
                  </span>
                  <span className="text-xs text-gray-500">
                    (
                    {
                      oscillatorIndicators.filter(
                        (ind) => visibleIndicators[ind.id]
                      ).length
                    }
                    )
                  </span>
                </div>
                {expandedSections.oscillators ? (
                  <ChevronUp className="h-4 w-4 text-gray-400" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-gray-400" />
                )}
              </button>
              {expandedSections.oscillators && (
                <div className="px-3 pb-3 space-y-2 border-t border-gray-100">
                  {oscillatorIndicators.map((indicator) => (
                    <div
                      key={indicator.id}
                      className="flex items-center justify-between py-1"
                    >
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id={indicator.id}
                          checked={visibleIndicators[indicator.id]}
                          onCheckedChange={() =>
                            handleIndicatorToggle(indicator.id)
                          }
                        />
                        <Label
                          htmlFor={indicator.id}
                          className="text-xs cursor-pointer flex-1"
                          style={{ color: indicator.color }}
                        >
                          {indicator.name}
                        </Label>
                      </div>
                      <div
                        className="h-2 w-2 rounded-full"
                        style={{ backgroundColor: indicator.color }}
                      ></div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Momentum & Volatility Section */}
            <div className="border border-gray-200 rounded-lg">
              <button
                onClick={() => toggleSection("momentum")}
                className="w-full p-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 bg-red-500 rounded-full"></div>
                  <span className="text-sm font-medium text-gray-700">
                    Momentum & Volatility
                  </span>
                  <span className="text-xs text-gray-500">
                    (
                    {
                      momentumIndicators.filter(
                        (ind) => visibleIndicators[ind.id]
                      ).length
                    }
                    )
                  </span>
                </div>
                {expandedSections.momentum ? (
                  <ChevronUp className="h-4 w-4 text-gray-400" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-gray-400" />
                )}
              </button>
              {expandedSections.momentum && (
                <div className="px-3 pb-3 space-y-2 border-t border-gray-100">
                  {momentumIndicators.map((indicator) => (
                    <div
                      key={indicator.id}
                      className="flex items-center justify-between py-1"
                    >
                      <div className="flex items-center space-x-2">
                        <Checkbox
                          id={indicator.id}
                          checked={visibleIndicators[indicator.id]}
                          onCheckedChange={() =>
                            handleIndicatorToggle(indicator.id)
                          }
                        />
                        <Label
                          htmlFor={indicator.id}
                          className="text-xs cursor-pointer flex-1"
                          style={{ color: indicator.color }}
                        >
                          {indicator.name}
                        </Label>
                      </div>
                      <div
                        className="h-2 w-2 rounded-full"
                        style={{ backgroundColor: indicator.color }}
                      ></div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Quick Actions */}
            <div className="pt-2 border-t border-gray-200">
              <div className="flex flex-wrap gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setExpandedSections({
                      movingAverages: true,
                      trendAnalysis: true,
                      macdFamily: true,
                      oscillators: true,
                      momentum: true,
                    });
                  }}
                  className="h-6 px-2 text-xs"
                >
                  Expand All
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setExpandedSections({
                      movingAverages: false,
                      trendAnalysis: false,
                      macdFamily: false,
                      oscillators: false,
                      momentum: false,
                    });
                  }}
                  className="h-6 px-2 text-xs"
                >
                  Collapse All
                </Button>
              </div>
            </div>

            {/* Enhanced Chart Options */}
            <div className="space-y-3 pt-3 border-t border-gray-200">
              <h4 className="text-sm font-medium text-gray-700 flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Chart Options
              </h4>

              {/* Chart Type Selection */}
              <div className="space-y-2">
                <Label className="text-xs font-medium text-gray-600">
                  Chart Type
                </Label>
                <ToggleGroup
                  type="single"
                  value={chartType}
                  onValueChange={(value) =>
                    value &&
                    setChartType(value as "line" | "area" | "candlestick")
                  }
                  size="sm"
                  className="grid grid-cols-3 gap-1 w-full"
                >
                  <ToggleGroupItem value="line" className="w-full h-8 text-xs">
                    Line
                  </ToggleGroupItem>
                  <ToggleGroupItem value="area" className="w-full h-8 text-xs">
                    Area
                  </ToggleGroupItem>
                  <ToggleGroupItem
                    value="candlestick"
                    className="w-full h-8 text-xs"
                  >
                    Candle
                  </ToggleGroupItem>
                </ToggleGroup>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div>
                    <Label htmlFor="scale-mode" className="text-sm font-medium">
                      Logarithmic Scale
                    </Label>
                    <div className="text-xs text-gray-500">
                      Better for large price ranges
                    </div>
                  </div>
                  <Switch
                    id="scale-mode"
                    checked={scale === "log"}
                    onCheckedChange={(checked) =>
                      setScale(checked ? "log" : "linear")
                    }
                  />
                </div>

                <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div>
                    <Label
                      htmlFor="volume-toggle"
                      className="text-sm font-medium"
                    >
                      Show Volume
                    </Label>
                    <div className="text-xs text-gray-500">
                      Display trading volume
                    </div>
                  </div>
                  <Switch
                    id="volume-toggle"
                    checked={showVolume}
                    onCheckedChange={setShowVolume}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col lg:ml-0">
        {/* Header */}
        <div className="bg-white border-b px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden"
            >
              <Menu className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-xl font-semibold capitalize text-gray-900">
                {selectedCoin} Analytics
              </h1>
              <p className="text-sm text-gray-600">
                Advanced technical analysis and price charts
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
              {getActiveIndicatorCount()} indicators active
            </div>

            {/* WebSocket Status */}
            <SimpleWebSocketStatus
              isConnected={isConnected && useRealTime}
              error={wsError}
              reconnectAttempts={reconnectAttempts}
            />

            {/* Real-time Toggle */}
            <div className="flex items-center gap-2">
              <Switch
                id="realtime-mode"
                checked={useRealTime}
                onCheckedChange={setUseRealTime}
              />
              <Label htmlFor="realtime-mode" className="text-xs">
                Real-time
              </Label>
            </div>
          </div>
        </div>

        {/* Chart Container */}
        <div className="flex-1 p-4">
          <Card className="h-full">
            <CardContent className="p-6 h-full">
              <div className="w-full h-full" style={{ minHeight: "500px" }}>
                {isLoading ? (
                  <ChartSkeleton />
                ) : error ? (
                  <div className="flex items-center justify-center h-full text-red-500">
                    <div className="text-center">
                      <WifiOff className="h-12 w-12 mx-auto mb-4 text-red-300" />
                      <h3 className="text-lg font-medium mb-2">
                        Error: {error}
                      </h3>
                      <p className="text-sm text-gray-500 mb-4">
                        {useRealTime && wsError
                          ? "Check your connection and try again"
                          : "Unable to fetch price data"}
                      </p>
                      <Button
                        onClick={() => window.location.reload()}
                        variant="outline"
                        className="gap-2"
                      >
                        <Wifi className="h-4 w-4" />
                        Retry
                      </Button>
                    </div>
                  </div>
                ) : prices.length > 0 ? (
                  <ResponsiveContainer>
                    {/* Render different chart types based on selection */}
                    {chartType === "area" ? (
                      <AreaChart data={prices}>
                        <defs>
                          <linearGradient
                            id="priceGradient"
                            x1="0"
                            y1="0"
                            x2="0"
                            y2="1"
                          >
                            <stop
                              offset="5%"
                              stopColor="#6366f1"
                              stopOpacity={0.8}
                            />
                            <stop
                              offset="95%"
                              stopColor="#6366f1"
                              stopOpacity={0.1}
                            />
                          </linearGradient>
                        </defs>
                        <CartesianGrid
                          strokeDasharray="3 3"
                          strokeOpacity={0.3}
                        />
                        <XAxis dataKey="timestamp" fontSize={12} />
                        <YAxis
                          yAxisId="left"
                          scale={scale}
                          domain={["auto", "auto"]}
                          fontSize={12}
                          tickFormatter={formatYAxisTick}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Area
                          yAxisId="left"
                          type="monotone"
                          dataKey="price_usd"
                          stroke="#6366f1"
                          strokeWidth={2}
                          fill="url(#priceGradient)"
                        />
                        {/* Include volume if enabled */}
                        {showVolume && (
                          <YAxis
                            yAxisId="volume"
                            orientation="right"
                            domain={[0, "dataMax"]}
                            fontSize={10}
                          />
                        )}
                        {showVolume && (
                          <Area
                            yAxisId="volume"
                            type="monotone"
                            dataKey="volume_24h"
                            stroke="#94a3b8"
                            strokeWidth={1}
                            fill="#e2e8f0"
                            fillOpacity={0.3}
                          />
                        )}
                        {/* Include indicators */}
                        {movingAverageIndicators.map(
                          (indicator) =>
                            visibleIndicators[indicator.id] && (
                              <Area
                                key={indicator.id}
                                yAxisId="left"
                                type="monotone"
                                dataKey={indicator.id}
                                stroke={indicator.color}
                                strokeWidth={1}
                                fill="none"
                              />
                            )
                        )}
                      </AreaChart>
                    ) : chartType === "candlestick" ? (
                      <ComposedChart data={prices}>
                        <CartesianGrid
                          strokeDasharray="3 3"
                          strokeOpacity={0.3}
                        />
                        <XAxis dataKey="timestamp" fontSize={12} />
                        <YAxis
                          yAxisId="left"
                          scale={scale}
                          domain={["auto", "auto"]}
                          fontSize={12}
                          tickFormatter={formatYAxisTick}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        {/* Candlestick representation using Area for high-low and Line for open-close */}
                        <Area
                          yAxisId="left"
                          type="monotone"
                          dataKey="price_usd"
                          stroke="#6366f1"
                          strokeWidth={2}
                          fill="none"
                        />
                        {/* Volume bars if enabled */}
                        {showVolume && (
                          <YAxis
                            yAxisId="volume"
                            orientation="right"
                            domain={[0, "dataMax"]}
                            fontSize={10}
                          />
                        )}
                        {showVolume && (
                          <Area
                            yAxisId="volume"
                            type="monotone"
                            dataKey="volume_24h"
                            stroke="#94a3b8"
                            strokeWidth={1}
                            fill="#e2e8f0"
                            fillOpacity={0.6}
                          />
                        )}
                        {/* Include indicators */}
                        {movingAverageIndicators.map(
                          (indicator) =>
                            visibleIndicators[indicator.id] && (
                              <Line
                                key={indicator.id}
                                yAxisId="left"
                                type="monotone"
                                dataKey={indicator.id}
                                stroke={indicator.color}
                                strokeWidth={1}
                                dot={false}
                              />
                            )
                        )}
                      </ComposedChart>
                    ) : (
                      /* Default Line Chart */
                      <LineChart data={prices}>
                        <CartesianGrid
                          strokeDasharray="3 3"
                          strokeOpacity={0.3}
                        />
                        <XAxis dataKey="timestamp" fontSize={12} />
                        <YAxis
                          yAxisId="left"
                          scale={scale}
                          domain={["auto", "auto"]}
                          fontSize={12}
                          tickFormatter={formatYAxisTick}
                        />
                        {/* Volume axis if enabled */}
                        {showVolume && (
                          <YAxis
                            yAxisId="volume"
                            orientation="right"
                            domain={[0, "dataMax"]}
                            fontSize={10}
                          />
                        )}
                        {/* Oscillator indicators Y-axis */}
                        {(visibleIndicators.rsi_14 ||
                          visibleIndicators.stochrsi_k ||
                          visibleIndicators.stochrsi_d ||
                          visibleIndicators.williams_r_14 ||
                          visibleIndicators.cci_20) && (
                          <YAxis
                            yAxisId="oscillator"
                            orientation="right"
                            domain={[0, 100]}
                            fontSize={10}
                          />
                        )}
                        <Tooltip content={<CustomTooltip />} />

                        {/* Main price line with enhanced styling */}
                        <Line
                          yAxisId="left"
                          type="monotone"
                          dataKey="price_usd"
                          name="Price"
                          stroke="#6366f1"
                          strokeWidth={3}
                          dot={false}
                          strokeLinecap="round"
                        />

                        {/* Volume bars if enabled */}
                        {showVolume && (
                          <Area
                            yAxisId="volume"
                            type="monotone"
                            dataKey="volume_24h"
                            stroke="#94a3b8"
                            strokeWidth={1}
                            fill="#e2e8f0"
                            fillOpacity={0.4}
                          />
                        )}

                        {/* Moving Average indicators */}
                        {movingAverageIndicators.map(
                          (indicator) =>
                            visibleIndicators[indicator.id] && (
                              <Line
                                key={indicator.id}
                                yAxisId="left"
                                type="monotone"
                                dataKey={indicator.id}
                                name={indicator.name}
                                stroke={indicator.color}
                                strokeWidth={2}
                                dot={false}
                                strokeDasharray={
                                  indicator.id.includes("ema") ? "5 5" : "none"
                                }
                              />
                            )
                        )}

                        {/* MACD indicators */}
                        {macdIndicators.map(
                          (indicator) =>
                            visibleIndicators[indicator.id] && (
                              <Line
                                key={indicator.id}
                                yAxisId="left"
                                type="monotone"
                                dataKey={indicator.id}
                                name={indicator.name}
                                stroke={indicator.color}
                                strokeWidth={2}
                                dot={false}
                              />
                            )
                        )}

                        {/* Trend indicators (except Bollinger Bands) */}
                        {trendIndicators
                          .filter((i) => i.id !== "bollinger_bands")
                          .map(
                            (indicator) =>
                              visibleIndicators[indicator.id] && (
                                <Line
                                  key={indicator.id}
                                  yAxisId="left"
                                  type="monotone"
                                  dataKey={indicator.id}
                                  name={indicator.name}
                                  stroke={indicator.color}
                                  strokeWidth={2}
                                  dot={false}
                                />
                              )
                          )}

                        {/* Momentum indicators */}
                        {momentumIndicators.map(
                          (indicator) =>
                            visibleIndicators[indicator.id] && (
                              <Line
                                key={indicator.id}
                                yAxisId="left"
                                type="monotone"
                                dataKey={indicator.id}
                                name={indicator.name}
                                stroke={indicator.color}
                                strokeWidth={2}
                                dot={false}
                              />
                            )
                        )}

                        {/* Bollinger Bands with enhanced styling */}
                        {visibleIndicators.bollinger_bands && (
                          <>
                            <Line
                              key="bb-upper"
                              yAxisId="left"
                              type="monotone"
                              dataKey="bb_upper"
                              name="BB Upper"
                              stroke="#8884d8"
                              strokeWidth={1}
                              strokeDasharray="4 4"
                              dot={false}
                              strokeOpacity={0.7}
                            />
                            <Line
                              key="bb-lower"
                              yAxisId="left"
                              type="monotone"
                              dataKey="bb_lower"
                              name="BB Lower"
                              stroke="#8884d8"
                              strokeWidth={1}
                              strokeDasharray="4 4"
                              dot={false}
                              strokeOpacity={0.7}
                            />
                            <Line
                              key="bb-mid"
                              yAxisId="left"
                              type="monotone"
                              dataKey="bb_mid"
                              name="BB Mid"
                              stroke="#8884d8"
                              strokeWidth={1}
                              strokeDasharray="2 2"
                              dot={false}
                              strokeOpacity={0.8}
                            />
                          </>
                        )}

                        {/* Oscillator indicators on separate axis */}
                        {oscillatorIndicators.map(
                          (indicator) =>
                            visibleIndicators[indicator.id] && (
                              <Line
                                key={indicator.id}
                                yAxisId="oscillator"
                                type="monotone"
                                dataKey={indicator.id}
                                name={indicator.name}
                                stroke={indicator.color}
                                strokeWidth={2}
                                dot={false}
                              />
                            )
                        )}

                        {/* Add reference lines for oscillators */}
                        {(visibleIndicators.rsi_14 ||
                          visibleIndicators.stochrsi_k ||
                          visibleIndicators.stochrsi_d) && (
                          <>
                            <ReferenceLine
                              yAxisId="oscillator"
                              y={70}
                              stroke="#ef4444"
                              strokeDasharray="2 2"
                              strokeOpacity={0.5}
                            />
                            <ReferenceLine
                              yAxisId="oscillator"
                              y={30}
                              stroke="#22c55e"
                              strokeDasharray="2 2"
                              strokeOpacity={0.5}
                            />
                          </>
                        )}

                        {/* Add brush for time navigation */}
                        <Brush dataKey="timestamp" height={30} fill="#f1f5f9" />
                      </LineChart>
                    )}
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-full text-slate-500">
                    No data available for the selected timeframe
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
