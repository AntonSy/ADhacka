"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api, Conference, Talk } from "@/lib/api";

export default function ArchivePage() {
  const [confs, setConfs] = useState<Conference[]>([]);
  const [conf, setConf] = useState("all");
  const [q, setQ] = useState("");
  const [data, setData] = useState<{ total: number; items: Talk[] }>({ total: 0, items: [] });

  useEffect(() => { api.conferences().then(setConfs).catch(() => {}); }, []);
  useEffect(() => {
    const t = setTimeout(() => api.talks({ conference: conf, q, limit: 500 }).then(setData).catch(() => {}), 200);
    return () => clearTimeout(t);
  }, [conf, q]);

  const withAnn = data.items.filter((t) => t.annotation).length;

  return (
    <Card>
      <CardHeader><CardTitle>Архив для сравнения</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground">
          Показано {data.items.length} из {data.total} принятых докладов. Аннотации загружены для {withAnn} из показанных. Слайды и видео не используются.
        </p>
        <div className="flex flex-wrap gap-2">
          <select
            className="h-10 rounded-md border border-input bg-card px-3 text-sm"
            value={conf}
            onChange={(e) => setConf(e.target.value)}
          >
            <option value="all">Все конференции</option>
            {confs.map((c) => (
              <option key={c.number} value={c.number}>Analyst Days {c.number} ({c.talks_count})</option>
            ))}
          </select>
          <Input className="flex-1" placeholder="Фильтр по названию, автору, компании" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <div className="overflow-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-muted-foreground"><th className="py-1">Конф.</th><th>Название</th><th>Автор</th><th>Компания</th></tr></thead>
            <tbody>
              {data.items.map((t) => (
                <tr key={t.id} className="border-t align-top">
                  <td className="py-1.5">{t.conference_number}</td>
                  <td>
                    {t.title}
                    {t.annotation && <span className="ml-2 rounded bg-indigo-50 px-1.5 py-0.5 text-xs text-indigo-800">есть аннотация</span>}
                  </td>
                  <td>{t.author_name}</td>
                  <td>{t.company}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
