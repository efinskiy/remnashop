import { Database, HardDrive } from "lucide-react";
import type { ComponentType } from "react";

import type { BackupKind } from "@entities/backups/api";
import { allValues } from "@shared/lib/all-values";

export const BACKUP_KINDS = allValues<BackupKind>()(["DATABASE", "ASSETS"]);

export const KIND_ICON: Record<BackupKind, ComponentType<{ className?: string }>> = {
  DATABASE: Database,
  ASSETS: HardDrive,
};
