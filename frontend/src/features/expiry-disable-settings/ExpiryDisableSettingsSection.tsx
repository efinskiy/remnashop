import { Power, PowerOff } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";

import { getGraceSettings, updateGraceSettings } from "@entities/settings/api";
import { usePermissions } from "@entities/user/use-current-user";
import { getErrorMessage } from "@shared/api/http";
import { blockNonIntegerKeys, parseRequiredInt } from "@shared/lib/number-input";
import { toast } from "@shared/lib/toast";
import { useAsyncResource } from "@shared/lib/use-async-resource";
import { ErrorState } from "@shared/ui/glass/EmptyState";
import { Field } from "@shared/ui/glass/Field";
import { Input } from "@shared/ui/glass/Input";
import { Row } from "@shared/ui/glass/Row";
import { Section, SectionFields, SectionRows } from "@shared/ui/glass/Section";
import { Switch } from "@shared/ui/glass/Switch";
import { SaveFooter } from "@shared/ui/SaveFooter";
import { Spinner } from "@shared/ui/Spinner";

// the backend's EXPIRY_DISABLE_MAX_DAYS
const MAX_DAYS = 3650;

export function ExpiryDisableSettingsSection() {
  const { t } = useTranslation();
  const canManage = usePermissions().includes("GRACE_SETTINGS_MANAGE");
  const [state, , setData] = useAsyncResource(getGraceSettings);
  const [enabled, setEnabled] = useState(false);
  const [afterDays, setAfterDays] = useState("7");
  const [warnDays, setWarnDays] = useState("2");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (state.kind !== "ready") return;
    setEnabled(state.data.expiry_disable_enabled);
    setAfterDays(String(state.data.expiry_disable_after_days));
    setWarnDays(String(state.data.expiry_disable_warn_days));
  }, [state]);

  const afterValue = parseRequiredInt(afterDays, 1);
  const parsedAfter = afterValue !== undefined && afterValue <= MAX_DAYS ? afterValue : undefined;
  const parsedWarn = parseRequiredInt(warnDays, 0);
  const warnTooLong = parsedAfter !== undefined && parsedWarn !== undefined && parsedWarn > parsedAfter;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (parsedAfter === undefined || parsedWarn === undefined || warnTooLong) return;
    setIsSubmitting(true);
    try {
      const settings = await updateGraceSettings({
        expiry_disable_enabled: enabled,
        expiry_disable_after_days: parsedAfter,
        expiry_disable_warn_days: parsedWarn,
      });
      setData(settings);
      toast.success(t("common.saved"));
    } catch (err) {
      toast.error(getErrorMessage(err, t("common.errors.generic")));
    } finally {
      setIsSubmitting(false);
    }
  };

  const saved = state.kind === "ready" ? state.data : null;
  const dirty =
    saved !== null &&
    (enabled !== saved.expiry_disable_enabled ||
      parsedAfter !== saved.expiry_disable_after_days ||
      parsedWarn !== saved.expiry_disable_warn_days);

  return (
    <form onSubmit={(event) => void handleSubmit(event)}>
      <Section
        icon={PowerOff}
        title={t("settings.expiryDisable.title")}
        description={t("settings.expiryDisable.description")}
        footer={state.kind === "ready" && canManage && <SaveFooter dirty={dirty} saving={isSubmitting} />}
      >
        {state.kind === "loading" && <Spinner size="card" />}
        {state.kind === "error" && <ErrorState text={t("common.loadError")} />}
        {state.kind === "ready" && (
          <fieldset disabled={!canManage} className="contents">
            <SectionRows>
              <Row
                icon={Power}
                label={t("settings.expiryDisable.enabledLabel")}
                hint={t("settings.expiryDisable.enabledHint")}
              >
                <Switch checked={enabled} onChange={setEnabled} />
              </Row>
            </SectionRows>
            <SectionFields flush>
              <Field
                label={t("settings.expiryDisable.afterDaysLabel")}
                htmlFor="expiry-disable-after"
                info={t("settings.expiryDisable.afterDaysHint")}
                error={
                  afterValue === undefined
                    ? t("errors.validation.min", { min: 1 })
                    : parsedAfter === undefined
                      ? t("errors.validation.max", { max: MAX_DAYS })
                      : undefined
                }
              >
                <Input
                  id="expiry-disable-after"
                  type="number"
                  onKeyDown={blockNonIntegerKeys}
                  step="1"
                  min="1"
                  max={MAX_DAYS}
                  value={afterDays}
                  onChange={(event) => setAfterDays(event.target.value)}
                />
              </Field>
              <Field
                label={t("settings.expiryDisable.warnDaysLabel")}
                htmlFor="expiry-disable-warn"
                info={t("settings.expiryDisable.warnDaysHint")}
                error={
                  parsedWarn === undefined
                    ? t("errors.validation.min", { min: 0 })
                    : warnTooLong
                      ? t("errors.validation.max", { max: parsedAfter })
                      : undefined
                }
              >
                <Input
                  id="expiry-disable-warn"
                  type="number"
                  onKeyDown={blockNonIntegerKeys}
                  step="1"
                  min="0"
                  value={warnDays}
                  onChange={(event) => setWarnDays(event.target.value)}
                />
              </Field>
            </SectionFields>
          </fieldset>
        )}
      </Section>
    </form>
  );
}
