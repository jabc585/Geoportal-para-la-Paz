import { useEffect, useState } from "react";
import { healthcheck } from "../../api/client";

export function StatusIndicator() {
  const [conectado, setConectado] = useState<boolean | null>(null);

  useEffect(() => {
    let activo = true;
    const verificar = () => {
      healthcheck().then((ok: boolean) => {
        if (activo) setConectado(ok);
      });
    };
    verificar();
    const intervalo = setInterval(verificar, 30000);
    return () => {
      activo = false;
      clearInterval(intervalo);
    };
  }, []);

  if (conectado === null) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
        <span className="w-1.5 h-1.5 rounded-full bg-yellow-400" />
        Verificando API…
      </span>
    );
  }

  if (conectado) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
        <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
        API conectada · actualizado hoy
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
      <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
      API no disponible
    </span>
  );
}
