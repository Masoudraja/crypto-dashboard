"use client";

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number; // Time to live in milliseconds
}

interface CacheOptions {
  ttl?: number; // Default TTL in milliseconds
  maxSize?: number; // Maximum number of entries
  enableLocalStorage?: boolean; // Persist to localStorage
}

class DataCache<T = any> {
  private cache = new Map<string, CacheEntry<T>>();
  private options: Required<CacheOptions>;
  private storageKey: string;

  constructor(name: string, options: CacheOptions = {}) {
    this.storageKey = `crypto-cache-${name}`;
    this.options = {
      ttl: options.ttl || 5 * 60 * 1000, // 5 minutes default
      maxSize: options.maxSize || 100,
      enableLocalStorage: options.enableLocalStorage ?? true,
    };

    // Load from localStorage if enabled
    if (this.options.enableLocalStorage) {
      this.loadFromStorage();
    }

    // Clean up expired entries periodically
    setInterval(() => this.cleanup(), 60000); // Every minute
  }

  set(key: string, data: T, customTtl?: number): void {
    const ttl = customTtl || this.options.ttl;
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      ttl,
    };

    // Remove oldest entry if cache is full
    if (this.cache.size >= this.options.maxSize) {
      const oldestKey = this.cache.keys().next().value;
      if (oldestKey) {
        this.cache.delete(oldestKey);
      }
    }

    this.cache.set(key, entry);

    // Save to localStorage if enabled
    if (this.options.enableLocalStorage) {
      this.saveToStorage();
    }
  }

  get(key: string): T | null {
    const entry = this.cache.get(key);

    if (!entry) {
      return null;
    }

    // Check if entry has expired
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  has(key: string): boolean {
    return this.get(key) !== null;
  }

  delete(key: string): boolean {
    const deleted = this.cache.delete(key);
    if (deleted && this.options.enableLocalStorage) {
      this.saveToStorage();
    }
    return deleted;
  }

  clear(): void {
    this.cache.clear();
    if (typeof window !== "undefined" && this.options.enableLocalStorage) {
      localStorage.removeItem(this.storageKey);
    }
  }

  size(): number {
    this.cleanup(); // Clean before reporting size
    return this.cache.size;
  }

  keys(): string[] {
    this.cleanup();
    return Array.from(this.cache.keys());
  }

  // Get or set pattern - common caching pattern
  async getOrSet<U extends T>(
    key: string,
    fetchFn: () => Promise<U>,
    customTtl?: number
  ): Promise<U> {
    const cached = this.get(key) as U;
    if (cached !== null) {
      return cached;
    }

    const data = await fetchFn();
    this.set(key, data, customTtl);
    return data;
  }

  // Batch operations
  mget(keys: string[]): Record<string, T | null> {
    const result: Record<string, T | null> = {};
    keys.forEach((key) => {
      result[key] = this.get(key);
    });
    return result;
  }

  mset(entries: Record<string, T>, customTtl?: number): void {
    Object.entries(entries).forEach(([key, data]) => {
      this.set(key, data, customTtl);
    });
  }

  private cleanup(): void {
    const now = Date.now();
    const expiredKeys: string[] = [];

    this.cache.forEach((entry, key) => {
      if (now - entry.timestamp > entry.ttl) {
        expiredKeys.push(key);
      }
    });

    expiredKeys.forEach((key) => this.cache.delete(key));

    if (expiredKeys.length > 0 && this.options.enableLocalStorage) {
      this.saveToStorage();
    }
  }

  private saveToStorage(): void {
    // Only access localStorage on the client side
    if (typeof window === "undefined" || !this.options.enableLocalStorage) {
      return;
    }

    try {
      const cacheData = Array.from(this.cache.entries());
      localStorage.setItem(this.storageKey, JSON.stringify(cacheData));
    } catch (error) {
      console.warn("Failed to save cache to localStorage:", error);
    }
  }

  private loadFromStorage(): void {
    // Only access localStorage on the client side
    if (typeof window === "undefined" || !this.options.enableLocalStorage) {
      return;
    }

    try {
      const stored = localStorage.getItem(this.storageKey);
      if (stored) {
        const cacheData: [string, CacheEntry<T>][] = JSON.parse(stored);
        this.cache = new Map(cacheData);
        this.cleanup(); // Remove any expired entries
      }
    } catch (error) {
      console.warn("Failed to load cache from localStorage:", error);
    }
  }

  // Cache statistics
  getStats() {
    let totalSize = 0;
    let expiredCount = 0;
    const now = Date.now();

    this.cache.forEach((entry) => {
      totalSize += JSON.stringify(entry.data).length;
      if (now - entry.timestamp > entry.ttl) {
        expiredCount++;
      }
    });

    return {
      totalEntries: this.cache.size,
      expiredEntries: expiredCount,
      totalSizeBytes: totalSize,
      maxSize: this.options.maxSize,
      defaultTtl: this.options.ttl,
    };
  }
}

// Predefined caches for different data types
export const priceCache = new DataCache("prices", {
  ttl: 30 * 1000, // 30 seconds for price data
  maxSize: 200,
});

export const coinListCache = new DataCache("coinlist", {
  ttl: 10 * 60 * 1000, // 10 minutes for coin list
  maxSize: 10,
});

export const newsCache = new DataCache("news", {
  ttl: 5 * 60 * 1000, // 5 minutes for news
  maxSize: 50,
});

export const analyticsCache = new DataCache("analytics", {
  ttl: 2 * 60 * 1000, // 2 minutes for analytics
  maxSize: 30,
});

export const marketDataCache = new DataCache("market", {
  ttl: 15 * 1000, // 15 seconds for market overview
  maxSize: 20,
});

// Cached API functions
interface PriceData {
  prices: any[];
}

interface NewsData {
  articles: any[];
}

interface CoinListData {
  coins: string[];
}

export async function getCachedPrices(
  coinId: string,
  timeframe: string = "7d"
): Promise<PriceData> {
  const cacheKey = `${coinId}-${timeframe}`;

  return priceCache.getOrSet(cacheKey, async () => {
    const response = await fetch(
      `http://localhost:8000/prices/${coinId}?timeframe=${timeframe}`
    );
    if (!response.ok) {
      throw new Error("Failed to fetch prices");
    }
    return response.json();
  });
}

export async function getCachedNews(
  search?: string,
  limit: number = 20,
  offset: number = 0
): Promise<NewsData> {
  const cacheKey = `news-${search || "all"}-${limit}-${offset}`;

  return newsCache.getOrSet(cacheKey, async () => {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });

    if (search) {
      params.append("search", search);
    }

    const response = await fetch(`http://localhost:8000/news?${params}`);
    if (!response.ok) {
      throw new Error("Failed to fetch news");
    }
    return response.json();
  });
}

export async function getCachedCoinList(): Promise<CoinListData> {
  return coinListCache.getOrSet("available-coins", async () => {
    const response = await fetch("http://localhost:8000/coins");
    if (!response.ok) {
      throw new Error("Failed to fetch coin list");
    }
    return response.json();
  });
}

export async function getCachedAnalytics(endpoint: string): Promise<any> {
  return analyticsCache.getOrSet(endpoint, async () => {
    const response = await fetch(`http://localhost:8000${endpoint}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch analytics: ${endpoint}`);
    }
    return response.json();
  });
}

export async function getCachedMarketData(): Promise<any> {
  return marketDataCache.getOrSet("overview", async () => {
    const response = await fetch("http://localhost:8000/sentiment");
    if (!response.ok) {
      throw new Error("Failed to fetch market data");
    }
    return response.json();
  });
}

// Cache management functions
export function clearAllCaches(): void {
  priceCache.clear();
  coinListCache.clear();
  newsCache.clear();
  analyticsCache.clear();
  marketDataCache.clear();
}

export function getCacheStats() {
  return {
    prices: priceCache.getStats(),
    coinlist: coinListCache.getStats(),
    news: newsCache.getStats(),
    analytics: analyticsCache.getStats(),
    marketData: marketDataCache.getStats(),
  };
}

// Preload commonly accessed data
export async function preloadCommonData(): Promise<void> {
  try {
    // Preload coin list
    await getCachedCoinList();

    // Preload market data
    await getCachedMarketData();

    // Preload latest news
    await getCachedNews(undefined, 10, 0);

    // Preload popular coins
    const popularCoins = ["bitcoin", "ethereum", "cardano", "solana"];
    await Promise.all(popularCoins.map((coin) => getCachedPrices(coin, "24h")));

    console.log("Common data preloaded successfully");
  } catch (error) {
    console.warn("Failed to preload some data:", error);
  }
}

// React hook for cache management
export function useCache() {
  const clearCache = (
    cacheType?: "all" | "prices" | "news" | "analytics" | "market"
  ) => {
    switch (cacheType) {
      case "prices":
        priceCache.clear();
        break;
      case "news":
        newsCache.clear();
        break;
      case "analytics":
        analyticsCache.clear();
        break;
      case "market":
        marketDataCache.clear();
        break;
      default:
        clearAllCaches();
    }
  };

  const getStats = () => getCacheStats();

  const preload = () => preloadCommonData();

  return {
    clearCache,
    getStats,
    preload,
  };
}
