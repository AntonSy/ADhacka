"use client";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, Application } from "@/lib/api";

export default function ApplicationsPage() {
  const [items, setItems] = useState<Application[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api.applications().then(setItems).catch(() => setFailed(true));
  }, []);

  return (
    <Card>
      <CardHeader><CardTitle>Поданные заявки</CardTitle></CardHeader>
      <CardContent>
        {failed ? (
          <p className="text-sm text-destructive">Не удалось загрузить заявки.</p>
        ) : items === null ? (
          <p className="text-sm text-muted-foreground">Загрузка…</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-muted-foreground">Заявок нет.</p>
        ) : (
          <table className="w-full text-sm">
            <thead><tr className="text-left text-muted-foreground"><th className="py-1">Дата</th><th>Название</th><th>Автор</th><th>Проверка</th><th>Уровень</th></tr></thead>
            <tbody>
              {items.map((a) => (
                <tr key={a.id} className="border-t">
                  <td className="py-1.5">{new Date(a.created_at).toLocaleString("ru-RU")}</td>
                  <td>{a.title}</td>
                  <td>{a.author_email}</td>
                  <td>{a.check_state}</td>
                  <td>{a.level ? <Badge variant={a.level === "LOW" ? "low" : a.level === "MEDIUM" ? "medium" : "high"}>{a.level}</Badge> : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </CardContent>
    </Card>
  );
}
