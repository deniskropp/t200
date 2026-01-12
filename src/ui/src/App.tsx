import { useState, useEffect } from "react";
import { TaskBoard } from "./components/TaskBoard";

type LogEntry = {
  topic: string;
  payload: any;
  timestamp: string;
  source: string;
};

function App() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [status, setStatus] = useState("disconnected");
  const [activeGoalId, setActiveGoalId] = useState<string | null>(null);
  const [mode, setMode] = useState<'ws' | 'sse'>('ws');

  useEffect(() => {
    let ws: WebSocket | null = null;
    let es: EventSource | null = null;

    if (mode === 'ws') {
        setStatus("connecting (ws)...");
        ws = new WebSocket("ws://localhost:8000/api/v1/logs/ws");
        ws.onopen = () => setStatus("connected (ws)");
        ws.onclose = () => setStatus("disconnected");
        ws.onmessage = (event) => handleMessage(JSON.parse(event.data));
    } else {
        setStatus("connecting (sse)...");
        es = new EventSource("http://localhost:8000/api/v1/stream/sse");
        es.onopen = () => setStatus("connected (sse)");
        es.onerror = () => setStatus("error (sse)"); // SSE auto-reconnects usually
        es.onmessage = (event) => handleMessage(JSON.parse(event.data));
    }

    const handleMessage = (data: any) => {
        // SSE wrapper might differ structure vs raw WS
        // Our backend SSE yields {event: "message", data: {topic...}}
        // EventSource.onmessage.data contains the JSON string of "data".
        // The `data` arg here is already JSON.parse(event.data).
        
        // Wait, for SSE `event.data` IS the payload string.
        // For WS `event.data` IS the payload string. 
        // Backend SSE yields `data` dict. JSON encoded.
        
        setLogs((prev) => [data, ...prev].slice(0, 50));
        if (data.topic === "workflow.goal_started") {
            setActiveGoalId(data.payload.id || data.payload.goal_id);
        }
    };

    return () => {
        if (ws) ws.close();
        if (es) es.close();
    };
  }, [mode]);

  return (
    <div className="p-8 bg-slate-900 min-h-screen text-slate-100 font-sans grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div className="space-y-6">
        <div>
            <h1 className="text-3xl font-bold mb-2 text-sky-400">OCS Orchestrator</h1>
            <div className="flex items-center gap-4 text-sm mb-2">
                <div>Status: <span className={status.includes("connected") ? "text-green-400" : "text-red-400"}>{status}</span></div>
                <div className="flex bg-slate-800 rounded p-1">
                    <button 
                        className={`px-3 py-1 rounded ${mode === 'ws' ? 'bg-sky-600' : 'hover:bg-slate-700'}`}
                        onClick={() => setMode('ws')}
                    >WS</button>
                    <button 
                        className={`px-3 py-1 rounded ${mode === 'sse' ? 'bg-sky-600' : 'hover:bg-slate-700'}`}
                        onClick={() => setMode('sse')}
                    >SSE</button>
                </div>
            </div>
            {activeGoalId && <div className="text-sky-200 text-sm">Active Goal: {activeGoalId}</div>}
        </div>

        <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 shadow-xl h-[600px] flex flex-col">
            <h2 className="text-xl font-semibold mb-2 text-sky-200">Task Board</h2>
            <div className="flex-1 overflow-hidden">
                <TaskBoard goalId={activeGoalId} />
            </div>
        </div>
      </div>

      <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 shadow-xl h-[700px] flex flex-col">
        <h2 className="text-xl font-semibold mb-2 text-sky-200">System Logs</h2>
        <div className="flex-1 overflow-y-auto font-mono text-sm space-y-2">
          {logs.length === 0 && <div className="text-slate-500 italic">No logs received yet...</div>}
          {logs.map((log, i) => (
            <div key={i} className="p-2 border-b border-slate-700 last:border-0 hover:bg-slate-700 transition">
              <div className="flex justify-between text-xs text-slate-400">
                <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                <span className="text-sky-300">[{log.source}]</span>
              </div>
              <div className="font-bold text-sky-500">{log.topic}</div>
              <pre className="text-slate-300 mt-1 overflow-x-auto">
                {JSON.stringify(log.payload, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
