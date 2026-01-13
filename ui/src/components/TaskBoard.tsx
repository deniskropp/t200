
import React, { useEffect, useState } from 'react';

interface Task {
  id: string;
  title: string;
  type: string;
  status: string;
  assigned_to: string | null;
}

interface TaskBoardProps {
  goalId: string | null;
}

export const TaskBoard: React.FC<TaskBoardProps> = ({ goalId }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchTasks = async () => {
    if (!goalId) return;
    try {
      const res = await fetch(`http://localhost:8000/api/v1/workflow/goals/${goalId}/tasks`);
      if (res.ok) {
        const data = await res.json();
        setTasks(data);
      }
    } catch (e) {
      console.error("Failed to fetch tasks", e);
    }
  };

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 2000); // Poll every 2s
    return () => clearInterval(interval);
  }, [goalId]);

  if (!goalId) return <div className="text-gray-500 text-center mt-10">Select or Start a Goal to see tasks</div>;

  const getColumnTasks = (statusFilter: string | string[]) => {
    const filters = Array.isArray(statusFilter) ? statusFilter : [statusFilter];
    return tasks.filter(t => filters.includes(t.status));
  };

  return (
    <div className="flex gap-4 p-4 h-full">
      <div className="flex-1 bg-gray-100 dark:bg-gray-800 p-4 rounded-lg">
        <h3 className="font-bold mb-4 text-gray-700 dark:text-gray-300">TODO / PENDING</h3>
        <div className="space-y-2">
            {getColumnTasks(['PENDING', 'Pending']).map(task => (
                <TaskCard key={task.id} task={task} />
            ))}
        </div>
      </div>
      
      <div className="flex-1 bg-blue-50 dark:bg-gray-700 p-4 rounded-lg border border-blue-100 dark:border-gray-600">
        <h3 className="font-bold mb-4 text-blue-700 dark:text-blue-300">IN PROGRESS</h3>
        <div className="space-y-2">
            {getColumnTasks(['IN_PROGRESS', 'Active', 'Working']).map(task => (
                <TaskCard key={task.id} task={task} />
            ))}
        </div>
      </div>
      
      <div className="flex-1 bg-green-50 dark:bg-gray-700 p-4 rounded-lg border border-green-100 dark:border-gray-600">
        <h3 className="font-bold mb-4 text-green-700 dark:text-green-300">COMPLETED</h3>
        <div className="space-y-2">
            {getColumnTasks(['COMPLETED', 'Completed', 'SUCCESS']).map(task => (
                <TaskCard key={task.id} task={task} />
            ))}
        </div>
      </div>
    </div>
  );
};

const TaskCard: React.FC<{ task: Task }> = ({ task }) => (
    <div className="bg-white dark:bg-gray-900 p-3 rounded shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="flex justify-between items-start">
            <h4 className="font-medium text-sm">{task.title}</h4>
            <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-500">
                {task.type}
            </span>
        </div>
        <div className="mt-2 text-xs text-gray-500 flex justify-between">
            <span>{task.assigned_to || 'Unassigned'}</span>
            <span>{task.status}</span>
        </div>
    </div>
);
