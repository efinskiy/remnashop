import { Globe } from "lucide-react";
import { useEffect, useId, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";

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

/** The zone the shop's days are counted in: the overview, analytics and the daily report. */
export function ShopTimezoneForm() {
  const { t } = useTranslation();
  const canManage = usePermissions().includes("SHOP_SETTINGS_MANAGE");
  const [state, , setData] = useAsyncResource(getShopSettings);
  const [timezone, setTimezone] = useState("UTC");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const id = useId();

  useEffect(() => {
    if (state.kind === "ready") setTimezone(state.data.timezone);
  }, [state]);

  const dirty = state.kind === "ready" && timezone !== state.data.timezone;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      const saved = await updateShopSettings({ timezone });
      setShopTimeZone(saved.timezone);
      setData(saved);
      toast.success(t("common.saved"));
    } catch (err) {
      toast.error(getErrorMessage(err, t("common.errors.generic")));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={(event) => void handleSubmit(event)}>
      <Section
        icon={Globe}
        title={t("settings.shopTimezone.title")}
        description={t("settings.shopTimezone.description")}
        footer={state.kind === "ready" && canManage && <SaveFooter dirty={dirty} saving={isSubmitting} />}
      >
        {state.kind === "loading" && <Spinner size="card" />}
        {state.kind === "error" && <ErrorState text={t("common.loadError")} />}
        {state.kind === "ready" && (
          <SectionFields>
            <Field label={t("settings.shopTimezone.timezone")} htmlFor={`${id}-timezone`}>
              <SelectDropdown
                variant="well"
                id={`${id}-timezone`}
                disabled={!canManage}
                value={timezone}
                onChange={setTimezone}
                icon={Globe}
                placeholder={timezone}
                options={TIME_ZONES}
              />
            </Field>
          </SectionFields>
        )}
      </Section>
    </form>
  );
}
