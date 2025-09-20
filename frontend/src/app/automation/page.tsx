"use client";

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Play,
  Pause,
  RefreshCw,
  Database,
  Newspaper,
  TrendingUp,
} from "lucide-react";

// --- Type Definitions ---
interface TaskStatus {
  task_name: string;
  status: "running" | "stopped" | "error" | "completed";
  last_run: string;
  next_run: string;
  success_count: number;
  error_count: number;
  last_error?: string;
}

interface SystemHealth {
  database_status: "connected" | "disconnected" | "error";
  api_status: "healthy" | "degraded" | "down";
  scheduler_status: "running" | "stopped";
  total_records: number;
  latest_update: string;
  uptime: string;
}

interface DataStats {
  total_price_records: number;
  total_news_articles: number;
  coins_tracked: number;
  last_data_update: string;
  update_frequency: string;
}

export default function AutomationPage() {
  const [tasks, setTasks] = useState<TaskStatus[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [dataStats, setDataStats] = useState<DataStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [controlLoading, setControlLoading] = useState<string | null>(null);

  // Handle task control actions (start/stop/run-once)
  const handleTaskControl = async (
    taskId: string,
    action: "start" | "stop" | "run-once"
  ) => {
    setControlLoading(`${taskId}-${action}`);
    try {
      const response = await fetch(
        `http://localhost:8000/api/automation/${action}/${taskId}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (response.ok) {
        const result = await response.json();
        console.log(result.message);
        // Refresh data immediately after action
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        const errorData = await response.json();
        setError(`Failed to ${action} task: ${errorData.detail}`);
      }
    } catch (e: any) {
      setError(`Error ${action} task: ${e.message}`);
    } finally {
      setControlLoading(null);
    }
  };

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const fetchData = async () => {
      try {
        setError(null);

        // Fetch automation status
        const response = await fetch(
          "http://localhost:8000/api/automation/status"
        );
        if (response.ok) {
          const data = await response.json();
          setTasks(data.tasks || []);
          setSystemHealth(data.system_health || null);
          setDataStats(data.data_stats || null);
        } else {
          // Fallback to individual health endpoint
          const healthResponse = await fetch("http://localhost:8000/health");
          if (healthResponse.ok) {
            const healthData = await healthResponse.json();
            setSystemHealth({
              database_status: "connected",
              api_status: "healthy",
              scheduler_status: "running",
              total_records: 0,
              latest_update: new Date().toISOString(),
              uptime: "0h 0m",
            });
          }
        }
      } catch (e: any) {
        setError(e.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "running":
      case "completed":
      case "healthy":
      case "connected":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "error":
      case "down":
      case "disconnected":
        return <XCircle className="h-4 w-4 text-red-500" />;
      case "stopped":
      case "degraded":
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const baseClasses = "text-xs font-medium";
    switch (status) {
      case "running":
      case "completed":
      case "healthy":
      case "connected":
        return (
          <Badge className={`${baseClasses} bg-green-100 text-green-800`}>
            {status}
          </Badge>
        );
      case "error":
      case "down":
      case "disconnected":
        return (
          <Badge className={`${baseClasses} bg-red-100 text-red-800`}>
            {status}
          </Badge>
        );
      case "stopped":
      case "degraded":
        return (
          <Badge className={`${baseClasses} bg-yellow-100 text-yellow-800`}>
            {status}
          </Badge>
        );
      default:
        return (
          <Badge className={`${baseClasses} bg-gray-100 text-gray-800`}>
            {status}
          </Badge>
        );
    }
  };

  const formatTime = (timestamp: string) => {
    if (!timestamp) return "Never";
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const calculateUptime = (uptime: string) => {
    // Simple uptime display - in real implementation, this would be calculated
    return uptime || "0h 0m";
  };

  if (isLoading) {
    return (
      <div className="p-4 md:p-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-slate-500">Loading automation status...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Automation Control</h1>
          <p className="text-slate-600">
            Monitor and control your crypto data collection system
          </p>
        </div>
        <Button
          onClick={() => window.location.reload()}
          variant="outline"
          className="gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {error && (
        <Card>
          <CardContent className="p-6">
            <div className="text-red-500 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              Error: {error}. The automation system may not be running.
            </div>
          </CardContent>
        </Card>
      )}

      {/* System Health Overview */}
      {systemHealth && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-600">Database</p>
                  <div className="flex items-center gap-2 mt-1">
                    {getStatusIcon(systemHealth.database_status)}
                    {getStatusBadge(systemHealth.database_status)}
                  </div>
                </div>
                <Database className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-600">
                    API Status
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    {getStatusIcon(systemHealth.api_status)}
                    {getStatusBadge(systemHealth.api_status)}
                  </div>
                </div>
                <Activity className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-600">
                    Scheduler
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    {getStatusIcon(systemHealth.scheduler_status)}
                    {getStatusBadge(systemHealth.scheduler_status)}
                  </div>
                </div>
                <Clock className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-600">Uptime</p>
                  <p className="text-lg font-bold">
                    {calculateUptime(systemHealth.uptime)}
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-indigo-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Data Statistics */}
      {dataStats && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              Data Collection Statistics
            </CardTitle>
            <CardDescription>
              Current status of your cryptocurrency data collection
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="text-center p-4 bg-slate-50 rounded-lg">
                <Database className="h-8 w-8 mx-auto mb-2 text-blue-500" />
                <p className="text-2xl font-bold">
                  {dataStats.total_price_records.toLocaleString()}
                </p>
                <p className="text-sm text-slate-600">Price Records</p>
              </div>

              <div className="text-center p-4 bg-slate-50 rounded-lg">
                <Newspaper className="h-8 w-8 mx-auto mb-2 text-green-500" />
                <p className="text-2xl font-bold">
                  {dataStats.total_news_articles.toLocaleString()}
                </p>
                <p className="text-sm text-slate-600">News Articles</p>
              </div>

              <div className="text-center p-4 bg-slate-50 rounded-lg">
                <TrendingUp className="h-8 w-8 mx-auto mb-2 text-purple-500" />
                <p className="text-2xl font-bold">{dataStats.coins_tracked}</p>
                <p className="text-sm text-slate-600">Coins Tracked</p>
              </div>

              <div className="text-center p-4 bg-slate-50 rounded-lg">
                <Clock className="h-8 w-8 mx-auto mb-2 text-orange-500" />
                <p className="text-sm font-bold">
                  {formatTime(dataStats.last_data_update)}
                </p>
                <p className="text-sm text-slate-600">Last Update</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Task Status */}
      <Tabs defaultValue="tasks" className="space-y-4">
        <TabsList>
          <TabsTrigger value="tasks">Task Status</TabsTrigger>
          <TabsTrigger value="schedule">Schedule</TabsTrigger>
          <TabsTrigger value="logs">Recent Activity</TabsTrigger>
        </TabsList>

        <TabsContent value="tasks" className="space-y-4">
          {tasks.length > 0 ? (
            <div className="grid gap-4">
              {tasks.map((task, index) => (
                <Card key={index}>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(task.status)}
                        <h3 className="font-semibold capitalize">
                          {task.task_name.replace("_", " ")}
                        </h3>
                        {getStatusBadge(task.status)}
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() =>
                            handleTaskControl(task.task_name, "start")
                          }
                        >
                          <Play className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() =>
                            handleTaskControl(task.task_name, "stop")
                          }
                        >
                          <Pause className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() =>
                            handleTaskControl(task.task_name, "run-once")
                          }
                        >
                          <RefreshCw className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-slate-600">Last Run</p>
                        <p className="font-medium">
                          {formatTime(task.last_run)}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-600">Next Run</p>
                        <p className="font-medium">
                          {formatTime(task.next_run)}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-600">Success Rate</p>
                        <div className="flex items-center gap-2">
                          <Progress
                            value={
                              (task.success_count /
                                (task.success_count + task.error_count)) *
                              100
                            }
                            className="flex-1"
                          />
                          <span className="font-medium">
                            {Math.round(
                              (task.success_count /
                                (task.success_count + task.error_count)) *
                                100
                            ) || 0}
                            %
                          </span>
                        </div>
                      </div>
                    </div>

                    {task.last_error && (
                      <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
                        <p className="text-sm text-red-700">
                          <strong>Last Error:</strong> {task.last_error}
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="p-6 text-center text-slate-500">
                No automation tasks configured. Run the task scheduler to see
                automation status.
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="schedule" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Automation Schedule</CardTitle>
              <CardDescription>
                Configured automation tasks and their frequencies
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div className="p-4 border rounded-lg">
                    <h4 className="font-semibold">Price Data Collection</h4>
                    <p className="text-sm text-slate-600 mt-1">
                      Every 5 minutes
                    </p>
                    <p className="text-xs text-slate-500 mt-2">
                      Fetches latest prices and calculates technical indicators
                    </p>
                  </div>

                  <div className="p-4 border rounded-lg">
                    <h4 className="font-semibold">News Aggregation</h4>
                    <p className="text-sm text-slate-600 mt-1">
                      Every 30 minutes
                    </p>
                    <p className="text-xs text-slate-500 mt-2">
                      Collects news from 7 RSS feeds and APIs
                    </p>
                  </div>

                  <div className="p-4 border rounded-lg">
                    <h4 className="font-semibold">Market Analysis</h4>
                    <p className="text-sm text-slate-600 mt-1">Every hour</p>
                    <p className="text-xs text-slate-500 mt-2">
                      Generates correlation matrix and volatility analysis
                    </p>
                  </div>

                  <div className="p-4 border rounded-lg">
                    <h4 className="font-semibold">Health Checks</h4>
                    <p className="text-sm text-slate-600 mt-1">Every 4 hours</p>
                    <p className="text-xs text-slate-500 mt-2">
                      Monitors system health and database status
                    </p>
                  </div>

                  <div className="p-4 border rounded-lg">
                    <h4 className="font-semibold">Daily Maintenance</h4>
                    <p className="text-sm text-slate-600 mt-1">
                      Daily at 1:00 AM
                    </p>
                    <p className="text-xs text-slate-500 mt-2">
                      Database cleanup and optimization
                    </p>
                  </div>

                  <div className="p-4 border rounded-lg">
                    <h4 className="font-semibold">Full Backfill</h4>
                    <p className="text-sm text-slate-600 mt-1">
                      Sundays at 2:00 AM
                    </p>
                    <p className="text-xs text-slate-500 mt-2">
                      Complete historical data refresh
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Recent Activity</CardTitle>
              <CardDescription>
                Latest automation tasks and system events
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center text-slate-500 py-8">
                <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>
                  Activity logs will appear here when the automation system is
                  running.
                </p>
                <p className="text-sm mt-2">
                  Start the task scheduler to see real-time activity.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
