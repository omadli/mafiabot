import { useQuery } from "@tanstack/react-query";
import axios from "axios";

interface HealthResponse {
  status: string;
  version: string;
  db: string;
}

async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await axios.get<HealthResponse>("/health");
  return data;
}

export function HealthCheck() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 5_000,
  });

  if (isLoading) return <div className="health-check">⏳ Backend tekshirilmoqda…</div>;

  if (isError) {
    return (
      <div className="health-check">
        <div className="status-fail">❌ Backend mavjud emas</div>
        <small>{error instanceof Error ? error.message : "Unknown error"}</small>
      </div>
    );
  }

  return (
    <div className="health-check">
      <div className={data?.status === "ok" ? "status-ok" : "status-fail"}>
        {data?.status === "ok" ? "✅" : "⚠️"} Backend: {data?.status} · DB: {data?.db}
      </div>
      <small>Version: {data?.version}</small>
    </div>
  );
}
