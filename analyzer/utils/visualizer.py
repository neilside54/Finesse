class MetricVisualizer:
    # Определяем пороги для каждой метрики
    # Формат: [порог_1, порог_2, порог_3, порог_4]
    # Например, для accuracy: если значение <35 -> 1 бар, >80 -> 5 бар
    THRESHOLDS = {
        "accuracy": [35, 50, 65, 80],
        "panic_rate": [30, 20, 10, 5],  # Чем ниже, тем лучше (reverse=True)
        "default": [20, 40, 60, 80]
    }

    @staticmethod
    def get_bars(value, peer_value, metric_type="accuracy", reverse=False):
        """
        value: текущее значение
        peer_value: среднее по пирам
        metric_type: ключ для выбора порогов из THRESHOLDS
        reverse: если True, то меньшее значение = лучше (например, цейтнот)
        """

        # 1. Определяем статус (сравнение с пирами)
        diff = value - peer_value

        if reverse:
            # Если reverse=True, то "better" — это меньшее значение (diff < 0)
            if diff < -2.0:
                status, color = "better", "green"
            elif diff > 2.0:
                status, color = "worse", "red"
            else:
                status, color = "equal", "yellow"
        else:
            # Стандарт: "better" — это большее значение (diff > 0)
            if diff > 2.0:
                status, color = "better", "green"
            elif diff < -2.0:
                status, color = "worse", "red"
            else:
                status, color = "equal", "yellow"

        # 2. Определяем количество полосок (визуализация)
        thresholds = MetricVisualizer.THRESHOLDS.get(metric_type, MetricVisualizer.THRESHOLDS["default"])

        bars = 1
        if reverse:
            # Логика для метрик, где меньше = лучше
            if value <= thresholds[3]:
                bars = 5
            elif value <= thresholds[2]:
                bars = 4
            elif value <= thresholds[1]:
                bars = 3
            elif value <= thresholds[0]:
                bars = 2
            else:
                bars = 1
        else:
            # Стандартная логика: больше = лучше
            if value > thresholds[3]:
                bars = 5
            elif value > thresholds[2]:
                bars = 4
            elif value > thresholds[1]:
                bars = 3
            elif value > thresholds[0]:
                bars = 2
            else:
                bars = 1

        return {
            "bars": bars,
            "status": status,
            "color": color
        }