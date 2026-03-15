/**
 * Zone API Client (STORY-1005)
 * API calls for multi-room zone management
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

// ---- Types ----

export interface ZoneMemberInfo {
  device_id: string;
  ip_address: string;
  role: "master" | "slave";
  name?: string;
  model?: string;
}

export interface ZoneInfo {
  master_id: string;
  master_ip: string;
  is_master: boolean;
  members: ZoneMemberInfo[];
}

// ---- API Functions ----

export async function getZones(): Promise<ZoneInfo[]> {
  const response = await fetch(`${API_BASE_URL}/api/zones`);
  if (!response.ok) {
    throw new Error(`Failed to fetch zones: ${response.statusText}`);
  }
  return response.json();
}

export async function getDeviceZone(deviceId: string): Promise<ZoneInfo | null> {
  const response = await fetch(`${API_BASE_URL}/api/devices/${encodeURIComponent(deviceId)}/zone`);
  if (!response.ok) {
    throw new Error(`Failed to fetch device zone: ${response.statusText}`);
  }
  return response.json();
}

export async function createZone(masterId: string, slaveIds: string[]): Promise<ZoneInfo> {
  const response = await fetch(`${API_BASE_URL}/api/zones`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ master_id: masterId, slave_ids: slaveIds }),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail || `Failed to create zone: ${response.statusText}`);
  }
  return response.json();
}

export async function dissolveZone(masterId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/zones/${encodeURIComponent(masterId)}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail || `Failed to dissolve zone: ${response.statusText}`);
  }
}

export async function addZoneMembers(masterId: string, deviceIds: string[]): Promise<ZoneInfo> {
  const response = await fetch(
    `${API_BASE_URL}/api/zones/${encodeURIComponent(masterId)}/members`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ device_ids: deviceIds }),
    }
  );
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail || `Failed to add members: ${response.statusText}`);
  }
  return response.json();
}

export async function removeZoneMembers(masterId: string, deviceIds: string[]): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/zones/${encodeURIComponent(masterId)}/members`,
    {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ device_ids: deviceIds }),
    }
  );
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail || `Failed to remove members: ${response.statusText}`);
  }
}

export async function changeMaster(
  currentMasterId: string,
  newMasterId: string
): Promise<ZoneInfo> {
  const response = await fetch(
    `${API_BASE_URL}/api/zones/${encodeURIComponent(currentMasterId)}/master`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_master_id: newMasterId }),
    }
  );
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.detail || `Failed to change master: ${response.statusText}`);
  }
  return response.json();
}
