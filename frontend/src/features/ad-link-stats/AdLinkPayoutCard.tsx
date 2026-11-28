import { useState } from "react";
import { useTranslation } from "react-i18next";

import { type AdLink, getAdLinkPayout } from "@entities/advertising/api";
import { shopToday, useShopTimeZoneReady } from "@entities/settings/shop-time-zone";
import { formatMoney } from "@shared/lib/format";
import { toIsoDate } from "@shared/lib/iso-date";
import { useAsyncResource } from "@shared/lib/use-async-resource";
import { EYEBROW_CLASS, GLASS_PLATE_CLASS } from "@shared/ui/classes";
import { DatePickerField } from "@shared/ui/DatePickerField";
import { ErrorState } from "@shared/ui/glass/EmptyState";
import { KpiTile } from "@shared/ui/KpiTile";
import { SegmentedPills } from "@shared/ui/SegmentedPills";
import { Spinner } from "@shared/ui/Spinner";

type Preset = "previous" | "current" | "custom";

// [first day, last day] of the shop's calendar month; offset 0 = this month
function monthRange(offset: number): [string, string] {
  const today = shopToday();
  const year = today.getFullYear();
  const month = today.getMonth() + offset;
  return [toIsoDate(new Date(year, month, 1)), toIsoDate(new Date(year, month + 1, 0))];
}

export function AdLinkPayoutCard({ adLink }: { adLink: AdLink }) {
  // the month presets are the shop's months
  return useShopTimeZoneReady() ? <AdLinkPayoutBody adLink={adLink} /> : <Spinner size="card" />;
}

function AdLinkPayoutBody({ adLink }: { adLink: AdLink }) {
  const { t, i18n } = useTranslation();
  const [preset, setPreset] = useState<Preset>("previous");
  const [customFrom, setCustomFrom] = useState(() => monthRange(0)[0]);
  const [customTo, setCustomTo] = useState(() => toIsoDate(shopToday()));

  const [from, to] =
    preset === "custom" ? [customFrom, customTo] : monthRange(preset === "previous" ? -1 : 0);
  const [state] = useAsyncResource((signal) => getAdLinkPayout(adLink.id, from, to, signal), {
    deps: [adLink.id, adLink.revenue_share_percent, from, to],
    keepData: true,
  });

  const range = new Intl.DateTimeFormat(i18n.language, { day: "numeric", month: "long", timeZone: "UTC" }).formatRange(
    new Date(`${from}T00:00:00Z`),
    new Date(`${to}T00:00:00Z`),
  );

  return (
    <div className={`${GLASS_PLATE_CLASS} flex flex-col gap-3 p-3.5`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className={EYEBROW_CLASS}>{t("advertising.payout.title")}</h3>
        <SegmentedPills
          compact
          value={preset}
          onChange={setPreset}
          options={[
            { value: "previous", label: t("advertising.payout.previousMonth") },
            { value: "current", label: t("advertising.payout.currentMonth") },
            { value: "custom", label: t("advertising.payout.custom") },
          ]}
        />
      </div>
      {preset === "custom" && (
        <div className="grid grid-cols-2 gap-3">
          <DatePickerField value={customFrom} onChange={setCustomFrom} placeholder={t("advertising.payout.from")} variant="well" />
          <DatePickerField value={customTo} onChange={setCustomTo} placeholder={t("advertising.payout.to")} variant="well" />
        </div>
      )}
      {state.kind === "loading" ? (
        <Spinner size="card" />
      ) : state.kind === "error" ? (
        <ErrorState text={t("common.loadError")} />
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <KpiTile glass label={t("advertising.payout.payments")} value={String(state.data.payments_count)} />
          <KpiTile
            glass
            label={t("advertising.payout.revenue")}
            value={formatMoney(state.data.revenue, state.data.report_currency, i18n.language)}
          />
          <KpiTile
            glass
            highlighted
            label={t("advertising.payout.toPay", { percent: Number(state.data.revenue_share_percent) })}
            value={formatMoney(state.data.payout, state.data.report_currency, i18n.language, true)}
          />
        </div>
      )}
      <p className="text-xs text-muted-foreground">{t("advertising.payout.footnote", { range })}</p>
    </div>
  );
}
