"use client";

import { cn } from "@/lib/utils";

// Base Skeleton Component
function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-slate-200", className)}
      {...props}
    />
  );
}

// Chart Skeleton
function ChartSkeleton() {
  return (
    <div className="w-full h-[500px] space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-6 w-24" />
      </div>
      <div className="relative h-[450px] bg-slate-50 rounded-lg p-4">
        <div className="absolute inset-4 space-y-4">
          {/* Y-axis labels */}
          <div className="absolute left-0 top-0 bottom-0 w-12 space-y-8">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-3 w-full" />
            ))}
          </div>

          {/* Chart area with animated lines */}
          <div className="ml-16 mr-4 h-full relative">
            <svg className="w-full h-full" viewBox="0 0 800 400">
              <defs>
                <linearGradient
                  id="skeleton-gradient"
                  x1="0%"
                  y1="0%"
                  x2="100%"
                  y2="0%"
                >
                  <stop offset="0%" stopColor="#e2e8f0" />
                  <stop offset="50%" stopColor="#cbd5e1" />
                  <stop offset="100%" stopColor="#e2e8f0" />
                </linearGradient>
              </defs>

              {/* Animated price line */}
              <path
                d="M0,200 Q200,150 400,180 T800,160"
                fill="none"
                stroke="url(#skeleton-gradient)"
                strokeWidth="3"
                className="animate-pulse"
              />

              {/* Grid lines */}
              {Array.from({ length: 5 }).map((_, i) => (
                <line
                  key={i}
                  x1="0"
                  y1={i * 80 + 40}
                  x2="800"
                  y2={i * 80 + 40}
                  stroke="#f1f5f9"
                  strokeWidth="1"
                />
              ))}
            </svg>
          </div>

          {/* X-axis labels */}
          <div className="ml-16 mr-4 flex justify-between">
            {Array.from({ length: 7 }).map((_, i) => (
              <Skeleton key={i} className="h-3 w-12" />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// Price Card Skeleton
function PriceCardSkeleton() {
  return (
    <div className="p-6 bg-white rounded-lg border space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Skeleton className="h-8 w-8 rounded-full" />
          <div className="space-y-2">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-3 w-12" />
          </div>
        </div>
        <Skeleton className="h-6 w-20" />
      </div>

      <div className="space-y-2">
        <Skeleton className="h-8 w-24" />
        <Skeleton className="h-4 w-16" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-4 w-20" />
        </div>
        <div className="space-y-1">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-4 w-20" />
        </div>
      </div>
    </div>
  );
}

// News Article Skeleton
function NewsArticleSkeleton() {
  return (
    <div className="p-6 border-b border-gray-200/50 space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 space-y-3">
          <Skeleton className="h-5 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <div className="space-y-2">
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-2/3" />
          </div>

          <div className="flex items-center gap-3">
            <Skeleton className="h-5 w-16" />
            <Skeleton className="h-3 w-12" />
            <Skeleton className="h-4 w-4 rounded-full" />
            <Skeleton className="h-3 w-16" />
          </div>
        </div>
        <Skeleton className="h-8 w-8" />
      </div>
    </div>
  );
}

// Table Row Skeleton
function TableRowSkeleton({ columns = 5 }: { columns?: number }) {
  return (
    <tr className="border-b">
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="p-4">
          <Skeleton className="h-4 w-full" />
        </td>
      ))}
    </tr>
  );
}

// Stats Card Skeleton
function StatsCardSkeleton() {
  return (
    <div className="p-6 bg-white rounded-lg border space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-24" />
        <Skeleton className="h-6 w-6 rounded" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-8 w-20" />
        <Skeleton className="h-3 w-16" />
      </div>
    </div>
  );
}

// Search Skeleton
function SearchSkeleton() {
  return (
    <div className="space-y-4">
      <div className="relative">
        <Skeleton className="h-10 w-full rounded-md" />
        <Skeleton className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4" />
      </div>

      {/* Search suggestions skeleton */}
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3 p-3 border rounded">
            <Skeleton className="h-6 w-6 rounded-full" />
            <Skeleton className="h-4 flex-1" />
            <Skeleton className="h-3 w-16" />
          </div>
        ))}
      </div>
    </div>
  );
}

// Advanced Analytics Skeleton
function AnalyticsSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-4 w-64" />
        </div>
        <Skeleton className="h-8 w-24" />
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <StatsCardSkeleton key={i} />
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartSkeleton />
        <ChartSkeleton />
      </div>
    </div>
  );
}

// Page Loading Skeleton
function PageSkeleton() {
  return (
    <div className="space-y-8 p-8">
      {/* Page Header */}
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96" />
      </div>

      {/* Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Sidebar */}
        <div className="space-y-6">
          <div className="space-y-3">
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-10 w-full" />
          </div>

          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-24" />
                <div className="space-y-1">
                  {Array.from({ length: 3 }).map((_, j) => (
                    <Skeleton key={j} className="h-3 w-full" />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3">
          <ChartSkeleton />
        </div>
      </div>
    </div>
  );
}

export {
  Skeleton,
  ChartSkeleton,
  PriceCardSkeleton,
  NewsArticleSkeleton,
  TableRowSkeleton,
  StatsCardSkeleton,
  SearchSkeleton,
  AnalyticsSkeleton,
  PageSkeleton,
};
