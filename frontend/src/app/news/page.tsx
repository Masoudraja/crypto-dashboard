"use client";

import { useState, useEffect, useMemo } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  ExternalLink,
  Newspaper,
  Search,
  Filter,
  TrendingUp,
  TrendingDown,
  Clock,
  Bookmark,
  Share2,
  Eye,
  BarChart3,
} from "lucide-react";
import { NewsArticleSkeleton } from "@/components/ui/skeleton";
import { getCachedNews } from "@/lib/cache";

// --- Enhanced ArticleData with more fields ---
interface ArticleData {
  title: string;
  link: string;
  published_date: string;
  source: string;
  summary?: string;
  sentiment?: "positive" | "negative" | "neutral";
  category?: string;
  reading_time?: number;
  engagement_score?: number;
}

// --- Skeleton Loading Component ---
function ArticleSkeleton() {
  return (
    <div className="p-4 border-b border-gray-200/50 animate-pulse">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-3">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="space-y-2">
            <div className="h-3 bg-gray-200 rounded w-full"></div>
            <div className="h-3 bg-gray-200 rounded w-2/3"></div>
          </div>
          <div className="flex items-center gap-3">
            <div className="h-5 bg-gray-200 rounded-full w-16"></div>
            <div className="h-3 bg-gray-200 rounded w-12"></div>
          </div>
        </div>
        <div className="h-8 w-8 bg-gray-200 rounded"></div>
      </div>
    </div>
  );
}

// --- Enhanced NewsItem component with modern features ---
function NewsItem({
  article,
  onBookmark,
}: {
  article: ArticleData;
  onBookmark: (article: ArticleData) => void;
}) {
  const [isBookmarked, setIsBookmarked] = useState(false);

  const getSourceColor = (source: string) => {
    const colors: Record<string, string> = {
      CoinTelegraph:
        "bg-blue-100 text-blue-800 border-blue-200 hover:bg-blue-200 hover:text-blue-900",
      CoinDesk:
        "bg-green-100 text-green-800 border-green-200 hover:bg-green-200 hover:text-green-900",
      Decrypt:
        "bg-purple-100 text-purple-800 border-purple-200 hover:bg-purple-200 hover:text-purple-900",
      CryptoSlate:
        "bg-orange-100 text-orange-800 border-orange-200 hover:bg-orange-200 hover:text-orange-900",
      BeInCrypto:
        "bg-red-100 text-red-800 border-red-200 hover:bg-red-200 hover:text-red-900",
      CryptoNews:
        "bg-yellow-100 text-yellow-800 border-yellow-200 hover:bg-yellow-200 hover:text-yellow-900",
      Blockworks:
        "bg-indigo-100 text-indigo-800 border-indigo-200 hover:bg-indigo-200 hover:text-indigo-900",
      CryptoPanic:
        "bg-pink-100 text-pink-800 border-pink-200 hover:bg-pink-200 hover:text-pink-900",
      NewsAPI:
        "bg-gray-100 text-gray-800 border-gray-200 hover:bg-gray-200 hover:text-gray-900",
    };
    return (
      colors[source] ||
      "bg-slate-100 text-slate-800 border-slate-200 hover:bg-slate-200 hover:text-slate-900"
    );
  };

  const getSentimentIcon = (sentiment?: string) => {
    switch (sentiment) {
      case "positive":
        return <TrendingUp className="h-3 w-3 text-green-500" />;
      case "negative":
        return <TrendingDown className="h-3 w-3 text-red-500" />;
      default:
        return <BarChart3 className="h-3 w-3 text-gray-500" />;
    }
  };

  const formatTimeAgo = (dateString: string) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffInMinutes = Math.floor(
        (now.getTime() - date.getTime()) / (1000 * 60)
      );

      if (diffInMinutes < 1) return "Just now";
      if (diffInMinutes < 60) return `${diffInMinutes}m ago`;

      const diffInHours = Math.floor(diffInMinutes / 60);
      if (diffInHours < 24) return `${diffInHours}h ago`;

      const diffInDays = Math.floor(diffInHours / 24);
      if (diffInDays === 1) return "Yesterday";
      if (diffInDays < 7) return `${diffInDays}d ago`;

      return date.toLocaleDateString();
    } catch {
      return new Date(dateString).toLocaleDateString();
    }
  };

  const handleBookmark = () => {
    setIsBookmarked(!isBookmarked);
    onBookmark(article);
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: article.title,
          url: article.link,
        });
      } catch (err) {
        // Fallback to clipboard
        navigator.clipboard.writeText(article.link);
      }
    } else {
      navigator.clipboard.writeText(article.link);
    }
  };

  return (
    <div className="group p-6 border-b last:border-b-0 border-gray-200/50 hover:bg-gradient-to-r hover:from-slate-50 hover:to-blue-50/30 transition-all duration-200">
      <div className="flex items-start justify-between gap-6">
        <div className="flex-1 min-w-0">
          <a
            href={article.link}
            target="_blank"
            rel="noopener noreferrer"
            className="block group/link"
          >
            <h3 className="font-semibold text-slate-800 group-hover/link:text-blue-600 transition-colors line-clamp-2 text-lg leading-relaxed mb-2">
              {article.title}
            </h3>
          </a>

          {article.summary && (
            <p className="text-sm text-slate-600 mt-2 line-clamp-2 leading-relaxed">
              {article.summary}
            </p>
          )}

          <div className="flex items-center justify-between mt-4">
            <div className="flex items-center gap-3 flex-wrap">
              <Badge className={`${getSourceColor(article.source)} border`}>
                {article.source}
              </Badge>

              <div className="flex items-center gap-1 text-xs text-slate-500">
                <Clock className="h-3 w-3" />
                {formatTimeAgo(article.published_date)}
              </div>

              {article.sentiment && (
                <div className="flex items-center gap-1">
                  {getSentimentIcon(article.sentiment)}
                  <span className="text-xs text-slate-500 capitalize">
                    {article.sentiment}
                  </span>
                </div>
              )}

              {article.reading_time && (
                <div className="flex items-center gap-1 text-xs text-slate-500">
                  <Eye className="h-3 w-3" />
                  {article.reading_time} min read
                </div>
              )}

              {article.category && (
                <Badge variant="outline" className="text-xs">
                  {article.category}
                </Badge>
              )}
            </div>
          </div>
        </div>

        <div className="flex-shrink-0 flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleBookmark}
            className={`opacity-0 group-hover:opacity-100 transition-opacity ${
              isBookmarked ? "text-blue-600" : "text-slate-400"
            }`}
          >
            <Bookmark
              className={`h-4 w-4 ${isBookmarked ? "fill-current" : ""}`}
            />
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={handleShare}
            className="opacity-0 group-hover:opacity-100 transition-opacity text-slate-400 hover:text-slate-600"
          >
            <Share2 className="h-4 w-4" />
          </Button>

          <a
            href={article.link}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-shrink-0 p-2 text-slate-400 hover:text-slate-600 transition-colors hover:bg-slate-100 rounded-md"
          >
            <ExternalLink className="h-4 w-4" />
          </a>
        </div>
      </div>
    </div>
  );
}

export default function NewsPage() {
  const [articles, setArticles] = useState<ArticleData[]>([]);
  const [bookmarkedArticles, setBookmarkedArticles] = useState<ArticleData[]>(
    []
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState<"newest" | "oldest" | "relevance">(
    "newest"
  );
  const [filterBySource, setFilterBySource] = useState<string>("all");
  const [filterByCategory, setFilterByCategory] = useState<string>("all");
  const [activeTab, setActiveTab] = useState("all");
  const ARTICLES_PER_PAGE = 15;

  // Mock data for demonstration (replace with real API data)
  const mockEnhanceArticle = (article: ArticleData): ArticleData => ({
    ...article,
    sentiment: ["positive", "negative", "neutral"][
      Math.floor(Math.random() * 3)
    ] as any,
    category: ["Bitcoin", "Ethereum", "DeFi", "NFTs", "Regulation", "Trading"][
      Math.floor(Math.random() * 6)
    ],
    reading_time: Math.floor(Math.random() * 8) + 1,
    engagement_score: Math.floor(Math.random() * 100),
  });

  // Get unique sources and categories for filters
  const availableSources = useMemo(() => {
    const sources = [...new Set(articles.map((article) => article.source))];
    return sources.sort();
  }, [articles]);

  const availableCategories = useMemo(() => {
    const categories = [
      ...new Set(articles.map((article) => article.category).filter(Boolean)),
    ];
    return categories.sort();
  }, [articles]);

  // Filter and sort articles
  const filteredAndSortedArticles = useMemo(() => {
    let filtered = articles;

    // Apply source filter
    if (filterBySource !== "all") {
      filtered = filtered.filter(
        (article) => article.source === filterBySource
      );
    }

    // Apply category filter
    if (filterByCategory !== "all") {
      filtered = filtered.filter(
        (article) => article.category === filterByCategory
      );
    }

    // Apply search filter
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (article) =>
          article.title.toLowerCase().includes(searchLower) ||
          article.source.toLowerCase().includes(searchLower) ||
          article.summary?.toLowerCase().includes(searchLower) ||
          article.category?.toLowerCase().includes(searchLower)
      );
    }

    // Apply sorting
    switch (sortBy) {
      case "newest":
        filtered.sort(
          (a, b) =>
            new Date(b.published_date).getTime() -
            new Date(a.published_date).getTime()
        );
        break;
      case "oldest":
        filtered.sort(
          (a, b) =>
            new Date(a.published_date).getTime() -
            new Date(b.published_date).getTime()
        );
        break;
      case "relevance":
        filtered.sort(
          (a, b) => (b.engagement_score || 0) - (a.engagement_score || 0)
        );
        break;
    }

    return filtered;
  }, [articles, filterBySource, filterByCategory, searchTerm, sortBy]);

  // Stats for the current filtered results
  const stats = useMemo(() => {
    const total = filteredAndSortedArticles.length;
    const sources = new Set(filteredAndSortedArticles.map((a) => a.source))
      .size;
    const categories = new Set(filteredAndSortedArticles.map((a) => a.category))
      .size;
    const sentiment = {
      positive: filteredAndSortedArticles.filter(
        (a) => a.sentiment === "positive"
      ).length,
      negative: filteredAndSortedArticles.filter(
        (a) => a.sentiment === "negative"
      ).length,
      neutral: filteredAndSortedArticles.filter(
        (a) => a.sentiment === "neutral"
      ).length,
    };
    return { total, sources, categories, sentiment };
  }, [filteredAndSortedArticles]);

  useEffect(() => {
    const fetchNews = async (isNewSearch: boolean) => {
      if (isNewSearch) {
        setIsLoading(true);
        setArticles([]);
      }
      setError(null);

      try {
        const offset = isNewSearch ? 0 : page * ARTICLES_PER_PAGE;
        const newsData = await getCachedNews(
          searchTerm,
          ARTICLES_PER_PAGE,
          offset
        );
        const enhancedArticles = newsData.articles.map(mockEnhanceArticle);

        setHasMore(enhancedArticles.length === ARTICLES_PER_PAGE);
        setArticles((prev) =>
          isNewSearch ? enhancedArticles : [...prev, ...enhancedArticles]
        );
      } catch (e: any) {
        setError(e.message);
      } finally {
        setIsLoading(false);
      }
    };

    const handler = setTimeout(() => {
      fetchNews(true);
    }, 500);

    return () => clearTimeout(handler);
  }, [searchTerm]);

  const loadMore = () => {
    setPage((prevPage) => prevPage + 1);
  };

  const handleBookmark = (article: ArticleData) => {
    setBookmarkedArticles((prev) => {
      const exists = prev.find((a) => a.link === article.link);
      if (exists) {
        return prev.filter((a) => a.link !== article.link);
      }
      return [...prev, article];
    });
  };

  const clearAllFilters = () => {
    setSearchTerm("");
    setFilterBySource("all");
    setFilterByCategory("all");
    setSortBy("newest");
  };

  useEffect(() => {
    if (page > 0) {
      const fetchMoreNews = async () => {
        setError(null);
        const offset = page * ARTICLES_PER_PAGE;
        try {
          const newsData = await getCachedNews(
            searchTerm,
            ARTICLES_PER_PAGE,
            offset
          );
          const enhancedArticles = newsData.articles.map(mockEnhanceArticle);
          setHasMore(enhancedArticles.length === ARTICLES_PER_PAGE);
          setArticles((prev) => [...prev, ...enhancedArticles]);
        } catch (e: any) {
          setError(e.message);
        }
      };
      fetchMoreNews();
    }
  }, [page]);

  const displayedArticles =
    activeTab === "bookmarked" ? bookmarkedArticles : filteredAndSortedArticles;

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto">
      {/* Header Section */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl text-white">
            <Newspaper className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-900">
              Crypto News Hub
            </h1>
            <p className="text-slate-600">
              Real-time cryptocurrency news from {availableSources.length}+
              trusted sources
            </p>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card className="p-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {stats.total}
              </div>
              <div className="text-sm text-slate-600">Articles</div>
            </div>
          </Card>
          <Card className="p-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {stats.sentiment.positive}
              </div>
              <div className="text-sm text-slate-600">Positive</div>
            </div>
          </Card>
          <Card className="p-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {stats.sentiment.negative}
              </div>
              <div className="text-sm text-slate-600">Negative</div>
            </div>
          </Card>
          <Card className="p-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {bookmarkedArticles.length}
              </div>
              <div className="text-sm text-slate-600">Bookmarked</div>
            </div>
          </Card>
        </div>
      </div>

      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="space-y-6"
      >
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="all">
            All News ({filteredAndSortedArticles.length})
          </TabsTrigger>
          <TabsTrigger value="bitcoin">Bitcoin</TabsTrigger>
          <TabsTrigger value="defi">DeFi</TabsTrigger>
          <TabsTrigger value="nfts">NFTs</TabsTrigger>
          <TabsTrigger value="bookmarked">
            Bookmarked ({bookmarkedArticles.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-6">
          {/* Search and Filters */}
          <Card className="p-6">
            <div className="space-y-4">
              {/* Search Bar */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search articles, sources, categories..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>

              {/* Filter Controls */}
              <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2">
                  <Filter className="h-4 w-4 text-slate-500" />
                  <span className="text-sm font-medium text-slate-700">
                    Filters:
                  </span>
                </div>

                <Select
                  value={sortBy}
                  onValueChange={(value: any) => setSortBy(value)}
                >
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="Sort by" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="newest">Newest First</SelectItem>
                    <SelectItem value="oldest">Oldest First</SelectItem>
                    <SelectItem value="relevance">Most Relevant</SelectItem>
                  </SelectContent>
                </Select>

                <Select
                  value={filterBySource}
                  onValueChange={setFilterBySource}
                >
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="Source" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Sources</SelectItem>
                    {availableSources.map((source) => (
                      <SelectItem key={source} value={source}>
                        {source}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Select
                  value={filterByCategory}
                  onValueChange={setFilterByCategory}
                >
                  <SelectTrigger className="w-40">
                    <SelectValue placeholder="Category" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Categories</SelectItem>
                    {availableCategories.map((category) =>
                      category ? (
                        <SelectItem key={category} value={category}>
                          {category}
                        </SelectItem>
                      ) : null
                    )}
                  </SelectContent>
                </Select>

                {(searchTerm ||
                  filterBySource !== "all" ||
                  filterByCategory !== "all" ||
                  sortBy !== "newest") && (
                  <Button variant="outline" size="sm" onClick={clearAllFilters}>
                    Clear Filters
                  </Button>
                )}
              </div>
            </div>
          </Card>

          {/* Articles List */}
          <Card className="overflow-hidden">
            {isLoading && articles.length === 0 ? (
              <div className="space-y-0">
                {Array.from({ length: 5 }).map((_, i) => (
                  <NewsArticleSkeleton key={i} />
                ))}
              </div>
            ) : error ? (
              <div className="p-8 text-center">
                <div className="text-red-500 mb-2">
                  ⚠️ Error loading articles
                </div>
                <p className="text-slate-600">{error}</p>
                <Button
                  className="mt-4"
                  onClick={() => window.location.reload()}
                >
                  Retry
                </Button>
              </div>
            ) : (
              <>
                {displayedArticles.length > 0 ? (
                  <div className="divide-y divide-gray-200/50">
                    {displayedArticles.map((article, index) => (
                      <NewsItem
                        key={`${article.link}-${index}`}
                        article={article}
                        onBookmark={handleBookmark}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="p-12 text-center">
                    <Newspaper className="h-12 w-12 mx-auto text-slate-300 mb-4" />
                    <h3 className="text-lg font-medium text-slate-900 mb-2">
                      No articles found
                    </h3>
                    <p className="text-slate-600 mb-4">
                      Try adjusting your search terms or filters
                    </p>
                    <Button variant="outline" onClick={clearAllFilters}>
                      Reset Filters
                    </Button>
                  </div>
                )}

                {hasMore && activeTab === "all" && (
                  <div className="p-6 text-center border-t">
                    <Button onClick={loadMore} variant="outline">
                      Load More Articles
                    </Button>
                  </div>
                )}
              </>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="bitcoin" className="space-y-6">
          <Card className="overflow-hidden">
            {filteredAndSortedArticles.filter(
              (article) =>
                article.category?.toLowerCase().includes("bitcoin") ||
                article.title.toLowerCase().includes("bitcoin") ||
                article.summary?.toLowerCase().includes("bitcoin")
            ).length > 0 ? (
              <div className="divide-y divide-gray-200/50">
                {filteredAndSortedArticles
                  .filter(
                    (article) =>
                      article.category?.toLowerCase().includes("bitcoin") ||
                      article.title.toLowerCase().includes("bitcoin") ||
                      article.summary?.toLowerCase().includes("bitcoin")
                  )
                  .map((article, index) => (
                    <NewsItem
                      key={`bitcoin-${article.link}-${index}`}
                      article={article}
                      onBookmark={handleBookmark}
                    />
                  ))}
              </div>
            ) : (
              <div className="p-12 text-center">
                <TrendingUp className="h-12 w-12 mx-auto text-orange-300 mb-4" />
                <h3 className="text-lg font-medium text-slate-900 mb-2">
                  No Bitcoin articles found
                </h3>
                <p className="text-slate-600">
                  Check back later for the latest Bitcoin news and updates
                </p>
              </div>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="defi" className="space-y-6">
          <Card className="overflow-hidden">
            {filteredAndSortedArticles.filter(
              (article) =>
                article.category?.toLowerCase().includes("defi") ||
                article.title.toLowerCase().includes("defi") ||
                article.summary?.toLowerCase().includes("defi") ||
                article.title.toLowerCase().includes("decentralized") ||
                article.summary?.toLowerCase().includes("decentralized")
            ).length > 0 ? (
              <div className="divide-y divide-gray-200/50">
                {filteredAndSortedArticles
                  .filter(
                    (article) =>
                      article.category?.toLowerCase().includes("defi") ||
                      article.title.toLowerCase().includes("defi") ||
                      article.summary?.toLowerCase().includes("defi") ||
                      article.title.toLowerCase().includes("decentralized") ||
                      article.summary?.toLowerCase().includes("decentralized")
                  )
                  .map((article, index) => (
                    <NewsItem
                      key={`defi-${article.link}-${index}`}
                      article={article}
                      onBookmark={handleBookmark}
                    />
                  ))}
              </div>
            ) : (
              <div className="p-12 text-center">
                <BarChart3 className="h-12 w-12 mx-auto text-blue-300 mb-4" />
                <h3 className="text-lg font-medium text-slate-900 mb-2">
                  No DeFi articles found
                </h3>
                <p className="text-slate-600">
                  Check back later for the latest DeFi and decentralized finance
                  news
                </p>
              </div>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="nfts" className="space-y-6">
          <Card className="overflow-hidden">
            {filteredAndSortedArticles.filter(
              (article) =>
                article.category?.toLowerCase().includes("nft") ||
                article.title.toLowerCase().includes("nft") ||
                article.summary?.toLowerCase().includes("nft") ||
                article.title.toLowerCase().includes("non-fungible") ||
                article.summary?.toLowerCase().includes("non-fungible")
            ).length > 0 ? (
              <div className="divide-y divide-gray-200/50">
                {filteredAndSortedArticles
                  .filter(
                    (article) =>
                      article.category?.toLowerCase().includes("nft") ||
                      article.title.toLowerCase().includes("nft") ||
                      article.summary?.toLowerCase().includes("nft") ||
                      article.title.toLowerCase().includes("non-fungible") ||
                      article.summary?.toLowerCase().includes("non-fungible")
                  )
                  .map((article, index) => (
                    <NewsItem
                      key={`nfts-${article.link}-${index}`}
                      article={article}
                      onBookmark={handleBookmark}
                    />
                  ))}
              </div>
            ) : (
              <div className="p-12 text-center">
                <div className="h-12 w-12 mx-auto text-purple-300 mb-4 flex items-center justify-center bg-purple-100 rounded-lg">
                  🎨
                </div>
                <h3 className="text-lg font-medium text-slate-900 mb-2">
                  No NFT articles found
                </h3>
                <p className="text-slate-600">
                  Check back later for the latest NFT and digital art news
                </p>
              </div>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="bookmarked" className="space-y-6">
          <Card className="overflow-hidden">
            {bookmarkedArticles.length > 0 ? (
              <div className="divide-y divide-gray-200/50">
                {bookmarkedArticles.map((article, index) => (
                  <NewsItem
                    key={`bookmark-${article.link}-${index}`}
                    article={article}
                    onBookmark={handleBookmark}
                  />
                ))}
              </div>
            ) : (
              <div className="p-12 text-center">
                <Bookmark className="h-12 w-12 mx-auto text-slate-300 mb-4" />
                <h3 className="text-lg font-medium text-slate-900 mb-2">
                  No bookmarked articles
                </h3>
                <p className="text-slate-600">
                  Bookmark articles from the "All News" tab to save them for
                  later reading
                </p>
              </div>
            )}
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
