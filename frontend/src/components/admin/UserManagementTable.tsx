import React from "react";
import { Button } from "../ui/Button";

interface UserItem {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: string;
  status: string;
  created_at: string;
  last_active: string | null;
  last_action: string | null;
}

interface UserTableProps {
  users: UserItem[];
  onUpdate: (id: number, role: string, status: string) => Promise<void>;
}

export function UserManagementTable({ users, onUpdate }: UserTableProps) {
  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case "admin":
        return "text-brand-cyan bg-brand-cyan/10 border-brand-cyan/20";
      case "officer":
        return "text-brand-blue bg-brand-blue/10 border-brand-blue/20";
      default:
        return "text-slate-400 bg-slate-500/10 border-slate-500/20";
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "Never";
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  return (
    <div className="overflow-x-auto rounded-lg border border-navy-accent/50 bg-navy-light">
      <table className="w-full text-left border-collapse text-sm text-slate-300">
        <thead>
          <tr className="bg-navy-dark border-b border-navy-accent/40 text-slate-400 font-semibold uppercase text-xs">
            <th className="p-4">User Info</th>
            <th className="p-4">Role / Permission</th>
            <th className="p-4">Status</th>
            <th className="p-4">Last Activity</th>
            <th className="p-4">Last Action</th>
            <th className="p-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-navy-accent/30">
          {users.map((user) => (
            <tr key={user.id} className="hover:bg-navy-dark/40 transition-colors">
              <td className="p-4">
                <div className="font-medium text-slate-100">{user.full_name}</div>
                <div className="text-xs text-slate-500 font-mono mt-0.5">{user.username} • {user.email}</div>
              </td>
              <td className="p-4">
                <span className={`px-2 py-0.5 text-xs font-mono font-semibold rounded border ${getRoleBadgeColor(user.role)}`}>
                  {user.role}
                </span>
              </td>
              <td className="p-4">
                <span className="flex items-center gap-1.5">
                  <span className={`w-2 h-2 rounded-full ${user.status === 'active' ? 'bg-status-green' : 'bg-status-red'}`} />
                  <span className="capitalize">{user.status}</span>
                </span>
              </td>
              <td className="p-4 text-slate-400">{formatDate(user.last_active)}</td>
              <td className="p-4 text-slate-400 max-w-[200px] truncate" title={user.last_action || ""}>
                {user.last_action || "None"}
              </td>
              <td className="p-4 text-right space-x-2">
                <select
                  value={user.role}
                  className="bg-navy-dark border border-navy-accent/50 text-slate-300 text-xs rounded p-1 hover:border-brand-cyan/40 focus:outline-none cursor-pointer"
                  onChange={(e) => onUpdate(user.id, e.target.value, user.status)}
                >
                  <option value="admin">Admin</option>
                  <option value="officer">Officer</option>
                  <option value="viewer">Viewer</option>
                </select>

                <select
                  value={user.status}
                  className="bg-navy-dark border border-navy-accent/50 text-slate-300 text-xs rounded p-1 hover:border-brand-cyan/40 focus:outline-none cursor-pointer"
                  onChange={(e) => onUpdate(user.id, user.role, e.target.value)}
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
