"use client";
import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { CheckResult } from "@/components/check-result";
import { api, Check, errorMessage } from "@/lib/api";

const MAX = 500;
const TEST_ANNOTATION =
  "Расскажу, как собирать техническое задание вместе с ИИ-ассистентом: от интервью с заказчиком и структуры документа до генерации требований, сценариев и описания API. Покажу промпты и шаблоны, типичные ошибки (галлюцинации, потеря контекста) и способ проверки результата по чек-листу. Сравним трудозатраты на ТЗ вручную и с ИИ и разберём, что нельзя отдавать модели.";;

export default function Page() {
  const [title, setTitle] = useState("");
  const [email, setEmail] = useState("");
  const [annotation, setAnnotation] = useState("");
  const [checkedText, setCheckedText] = useState<string | null>(null);
  const [check, setCheck] = useState<Check | null>(null);
  const [history, setHistory] = useState<Check[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [submitMsg, setSubmitMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const areaRef = useRef<HTMLTextAreaElement>(null);

  const len = annotation.length;
  const tooLong = len > MAX;
  const stale = check !== null && checkedText !== annotation;

  async function runCheck() {
    setBusy(true);
    setError("");
    try {
      const res = await api.createCheck(annotation, title);
      setCheck(res);
      setCheckedText(annotation);
      setHistory((h) => [res, ...h.filter((x) => x.id !== res.id)]);
      setTimeout(() => document.getElementById("result")?.scrollIntoView({ behavior: "smooth" }), 50);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }

  function validForm(): boolean {
    if (!title.trim()) { setSubmitMsg({ ok: false, text: "Укажите название доклада." }); return false; }
    if (!/.+@.+\..+/.test(email)) { setSubmitMsg({ ok: false, text: "Укажите корректный e-mail." }); return false; }
    if (len < 1 || tooLong) { setSubmitMsg({ ok: false, text: "Аннотация должна содержать от 1 до 500 символов." }); return false; }
    return true;
  }

  async function submit(withCheck: boolean) {
    setSubmitMsg(null);
    if (!validForm()) return;
    if (withCheck) {
      if (!check) { setSubmitMsg({ ok: false, text: "Проверка ещё не выполнена. Нажмите «Проверить» или «Подать без проверки»." }); return; }
      if (stale) { setSubmitMsg({ ok: false, text: "Аннотация изменилась после проверки. Перепроверьте её." }); return; }
      if (check.level === "HIGH" && !confirm("Найдено высокое пересечение. Подать всё равно?")) return;
    } else if (!confirm("Не проверено на пересечения с архивом. Подать без проверки?")) return;
    try {
      await api.createApplication({ title, annotation, email, check_id: withCheck && check ? check.id : null });
      setSubmitMsg({ ok: true, text: withCheck ? "Заявка подана. Проверка привязана к заявке." : "Заявка подана со статусом not_checked." });
    } catch (e) {
      setSubmitMsg({ ok: false, text: errorMessage(e) });
    }
  }

  return (
    <>
      <Card>
        <CardHeader><CardTitle>Новая заявка</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="title">Название доклада</Label>
            <Input id="title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Например: Как писать ТЗ с помощью ИИ" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="email">E-mail автора</Label>
            <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="author@example.com" />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ann">Аннотация (до 500 символов)</Label>
            <Textarea id="ann" ref={areaRef} value={annotation} onChange={(e) => setAnnotation(e.target.value)} placeholder="Кратко опишите, о чём ваш доклад" />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button onClick={runCheck} disabled={busy || len < 1 || tooLong}>{busy ? "Идёт проверка…" : "Проверить"}</Button>
            <Button variant="outline" onClick={() => { setAnnotation(TEST_ANNOTATION); setTitle("Как писать ТЗ с помощью ИИ"); }}>
              Вставить тестовую аннотацию
            </Button>
            <span className={`ml-auto text-sm ${tooLong ? "font-bold text-destructive" : "text-muted-foreground"}`}>{len}/{MAX}</span>
          </div>
          {tooLong && <p className="text-sm text-destructive">Максимум 500 символов</p>}
          {error && (
            <div className="flex flex-wrap items-center gap-2 rounded-md border border-red-300 bg-red-50 p-3 text-sm">
              <span>{error}</span>
              <Button variant="outline" size="sm" onClick={runCheck}>Повторить</Button>
              <Button variant="outline" size="sm" onClick={() => submit(false)}>Подать без проверки</Button>
            </div>
          )}
        </CardContent>
      </Card>

      {check && <CheckResult check={check} stale={stale} onEdit={() => areaRef.current?.focus()} />}

      <Card>
        <CardHeader><CardTitle>История проверок сессии</CardTitle></CardHeader>
        <CardContent>
          {history.length === 0 ? (
            <p className="text-sm text-muted-foreground">Пока пусто.</p>
          ) : (
            <table className="w-full text-sm">
              <thead><tr className="text-left text-muted-foreground"><th className="py-1">Время</th><th>Уровень</th><th>Score</th><th>Первое совпадение</th><th></th></tr></thead>
              <tbody>
                {history.map((c) => (
                  <tr key={c.id} className="border-t">
                    <td className="py-1.5">{new Date(c.created_at).toLocaleTimeString("ru-RU")}</td>
                    <td><Badge variant={c.level === "LOW" ? "low" : c.level === "MEDIUM" ? "medium" : "high"}>{c.level}</Badge></td>
                    <td>{c.top_score.toFixed(2)}</td>
                    <td>{c.matches[0]?.title ?? "—"}</td>
                    <td><button className="text-primary underline" onClick={() => setCheck(c)}>открыть</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="space-y-2 p-5 text-right">
          <Button onClick={() => submit(true)}>Подать заявку</Button>{" "}
          <Button variant="outline" onClick={() => submit(false)}>Подать без проверки</Button>
          {submitMsg && (
            <div className={`rounded-md border p-3 text-left text-sm ${submitMsg.ok ? "border-emerald-300 bg-emerald-50" : "border-red-300 bg-red-50"}`}>
              {submitMsg.text}
            </div>
          )}
        </CardContent>
      </Card>
    </>
  );
}
