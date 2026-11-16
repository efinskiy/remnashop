import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";

import { usePermissions } from "@entities/user/use-current-user";
import { PillTabs } from "@shared/ui/PillTabs";

type TransactionsTab = "orders" | "recurring";

const TAB_PATHS: Record<TransactionsTab, string> = {
  orders: "/dashboard/transactions",
  recurring: "/dashboard/transactions/recurring",
};

/** Orders | auto-renewals: shown only to someone who may open both. */
export function TransactionsTabs({ active }: { active: TransactionsTab }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const permissions = usePermissions();
  if (!permissions.includes("TRANSACTIONS_VIEW") || !permissions.includes("TRANSACTIONS_RECURRING_VIEW")) {
    return null;
  }
  return (
    <div className="shrink-0">
      <PillTabs
        items={(["orders", "recurring"] as const).map((key) => ({ key, label: t(`transactions.tabs.${key}`) }))}
        activeKey={active}
        onSelect={(key) => navigate(TAB_PATHS[key])}
      />
    </div>
  );
}
