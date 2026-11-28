import { CalendarClock, Clock, Globe } from "lucide-react";
import { useEffect, useId, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";

import { getNotificationSettings, updateNotificationSettings } from "@entities/notifications/api";
import { getShopSettings, updateShopSettings } from "@entities/settings/api";
import { setShopTimeZone } from "@entities/settings/shop-time-zone";
import { usePermissions } from "@entities/user/use-current-user";
import { getErrorMessage } from "@shared/api/http";
import { toast } from "@shared/lib/toast";
import { useAsyncResource } from "@shared/lib/use-async-resource";
import { ErrorState } from "@shared/ui/glass/EmptyState";
import { Field } from "@shared/ui/glass/Field";
import { Section, SectionFields } from "@shared/ui/glass/Section";
import { SaveFooter } from "@shared/ui/SaveFooter";
import { SelectDropdown } from "@shared/ui/SelectDropdown";
import { Spinner } from "@shared/ui/Spinner";

const TIME_ZONES = ["UTC", ...Intl.supportedValuesOf("timeZone").filter((zone) => zone !== "UTC")].map((zone) => ({
  value: zone,
  label: zone,
}));
const HOURS = Array.from({ length: 24 }, (_, hour) => ({
  value: String(hour),
  label: `${String(hour).padStart(2, "0")}:00`,
}));

/** The shop's time zone and the daily report's hour: two settings, each behind its own permissions. */
export function TimeSettingsForm() {
  const { t } = useTranslation();
  const permissions = usePermissions();
  const canViewZone = permissions.includes("SHOP_SETTINGS_VIEW");
  const canManageZone = permissions.includes("SHOP_SETTINGS_MANAGE");
  const canViewHour = permissions.includes("NOTIFICATION_SETTINGS_VIEW");
  const canManageHour = permissions.includes("NOTIFICATION_SETTINGS_MANAGE");
  const [shopState, , setShop] = useAsyncResource((signal) => (canViewZone ? getShopSettings(signal) : Promise.resolve(null)), {
    deps: [canViewZone],
  });
  const [reportState, , setReport] = useAsyncResource(
    (signal) => (canViewHour ? getNotificationSettings(signal) : Promise.resolve(null)),
    { deps: [canViewHour] },
  );
  const [timezone, setTimezone] = useState("UTC");
  const [hour, setHour] = useState("0");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const id = useId();

  const shop = shopState.kind === "ready" ? shopState.data : null;
  const report = reportState.kind === "ready" ? reportState.data : null;

  useEffect(() => {
    if (shop) setTimezone(shop.timezone);
  }, [shop]);
  useEffect(() => {
    if (report) setHour(String(report.daily_report_hour));
  }, [report]);

  const zoneDirty = shop !== null && timezone !== shop.timezone;
  const hourDirty = report !== null && hour !== String(report.daily_report_hour);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      if (zoneDirty) {
        const saved = await updateShopSettings({ timezone });
        setShopTimeZone(saved.timezone);
        setShop(saved);
      }
      if (hourDirty) setReport(await updateNotificationSettings({ daily_report_hour: Number(hour) }));
      toast.success(t("common.saved"));
    } catch (err) {
      toast.error(getErrorMessage(err, t("common.errors.generic")));
    } finally {
      setIsSubmitting(false);
    }
  };

  const loading = shopState.kind === "loading" || reportState.kind === "loading";
  const failed = shopState.kind === "error" || reportState.kind === "error";
  const canManage = (shop !== null && canManageZone) || (report !== null && canManageHour);

  return (
    <form onSubmit={(event) => void handleSubmit(event)}>
      <Section
        icon={CalendarClock}
        title={t("settings.time.title")}
        description={t("settings.time.description")}
        footer={!loading && !failed && canManage && <SaveFooter dirty={zoneDirty || hourDirty} saving={isSubmitting} />}
      >
        {loading && <Spinner size="card" />}
        {!loading && failed && <ErrorState text={t("common.loadError")} />}
        {!loading && !failed && (
          <SectionFields>
            {shop !== null && (
              <Field label={t("settings.time.timezone")} htmlFor={`${id}-timezone`}>
                <SelectDropdown
                  variant="well"
                  id={`${id}-timezone`}
                  disabled={!canManageZone}
                  value={timezone}
                  onChange={setTimezone}
                  icon={Globe}
                  placeholder={timezone}
                  options={TIME_ZONES}
                />
              </Field>
            )}
            {report !== null && (
              <Field label={t("settings.time.reportHour")} htmlFor={`${id}-hour`}>
                <SelectDropdown
                  variant="well"
                  id={`${id}-hour`}
                  disabled={!canManageHour}
                  value={hour}
                  onChange={setHour}
                  icon={Clock}
                  placeholder={HOURS[Number(hour)].label}
                  options={HOURS}
                />
              </Field>
            )}
          </SectionFields>
        )}
      </Section>
    </form>
  );
}
