"use client";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api, Check, Level } from "@/lib/api";

const LABEL: Record<Level, string> = {
  LOW: "Существенных пересечений не найдено",
  MEDIUM: "Частичное пересечение с ранее принятыми докладами",
  HIGH: "Похожая тема уже была",
};
const VARIANT = { LOW: "low", MEDIUM: "medium", HIGH: "high" } as const;
const BAR = { LOW: "bg-emerald-600", MEDIUM: "bg-amber-600", HIGH: "bg-red-600" } as const;

export function CheckResult({ check, stale, onEdit }: { check: Check; stale: boolean; onEdit: () => void }) {
  const [open, setOpen] = useState<string | null>(null);
  const [vote, setVote] = useState<boolean | null>(null);
  const [comment, setComment] = useState("");
  const [sent, setSent] = useState(false);
  const shown = check.matches.slice(0, check.level === "LOW" ? 3 : 5);

  async function sendVote(v: boolean) {
    setVote(v);
    setSent(false);
    try { await api.feedback(check.id, v); } catch {}
  }
  async function sendComment() {
    if (vote === null) return;
    try { await api.feedback(check.id, vote, comment); } catch {}
    setSent(true);
  }

  return (
    <Card id="result">
      <CardHeader><CardTitle>Результат проверки</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        {stale && (
          <div className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm">
            Аннотация изменилась после проверки: результат устарел. Нажмите «Проверить».
          </div>
        )}
        <div className="flex flex-wrap items-center gap-3">
          <Badge variant={VARIANT[check.level]}>{check.level}</Badge>
          <b>{LABEL[check.level]}</b>
          <div className="h-2 w-48 overflow-hidden rounded bg-secondary">
            <div className={`h-full ${BAR[check.level]}`} style={{ width: `${Math.min(100, check.top_score * 100)}%` }} />
          </div>
          <span className="text-xs text-muted-foreground">score {check.top_score.toFixed(2)}</span>
          {check.cached && <span className="text-xs text-muted-foreground">(из кэша)</span>}
        </div>
        {check.level === "HIGH" && (
          <div className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm">
            Подача не блокируется, но рассмотрите другой ракурс темы.
          </div>
        )}
        {shown.length === 0 ? (
          <p className="text-sm text-muted-foreground">Похожие доклады не найдены.</p>
        ) : (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold">{check.level === "LOW" ? "Ближайшие доклады для справки" : "Похожие доклады"}</h4>
            {shown.map((m) => (
              <div key={m.talk_id} className="rounded-md border p-3">
                <button className="text-left font-semibold" onClick={() => setOpen(open === m.talk_id ? null : m.talk_id)}>
                  {m.title}
                </button>
                <div className="text-xs text-muted-foreground">
                  Analyst Days {m.conference_number}, {m.year} · {m.author}{m.company ? `, ${m.company}` : ""} · сходство {m.score.toFixed(2)}
                </div>
                <div className="mt-1 flex flex-wrap gap-1">
                  {m.matched_aspects.map((a) => (
                    <span key={a} className="rounded bg-indigo-50 px-2 py-0.5 text-xs text-indigo-800">{a}</span>
                  ))}
                </div>
                {open === m.talk_id && (
                  <div className="mt-2 border-t border-dashed pt-2 text-sm">
                    {m.city && <div>Город: {m.city}{m.format ? `; формат: ${m.format}` : ""}</div>}
                    <div>
                      Аннотация:{" "}
                      {m.annotation ?? <i className="text-muted-foreground">в данных отсутствует (загружено только название)</i>}
                    </div>
                    {m.url && (
                      <a className="text-primary underline" href={m.url} target="_blank" rel="noopener noreferrer">
                        Открыть в архиве
                      </a>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        {check.recommendation && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold">
              Как доработать тему <span className="font-normal text-muted-foreground">(источник: {check.recommendation_source})</span>
            </h4>
            <p className="text-sm">{check.recommendation}</p>
            <Button variant="outline" size="sm" onClick={onEdit}>Исправить аннотацию</Button>
          </div>
        )}
        <div className="space-y-2">
          <h4 className="text-sm font-semibold">Была ли проверка полезной?</h4>
          <div className="flex flex-wrap items-center gap-2">
            <Button variant={vote === true ? "default" : "outline"} size="sm" onClick={() => sendVote(true)}>Полезно</Button>
            <Button variant={vote === false ? "default" : "outline"} size="sm" onClick={() => sendVote(false)}>Не полезно</Button>
          </div>
          {vote !== null && !sent && (
            <div className="flex gap-2">
              <Input placeholder="Комментарий (необязательно)" value={comment} onChange={(e) => setComment(e.target.value)} />
              <Button variant="outline" onClick={sendComment}>Отправить</Button>
            </div>
          )}
          {sent && <p className="text-sm text-muted-foreground">Спасибо за отзыв</p>}
        </div>
      </CardContent>
    </Card>
  );
}
