/**
 * useRoutePlanner — composable managing optimal-path routing UI state.
 * GRF-01, GRF-03, GRF-04, GRF-07.
 */

import { computed, ref, watch } from "vue";
import { useRouteStore, type RoutingAlgorithm } from "@/stores/routeStore";

export function useRoutePlanner() {
  const store = useRouteStore();

  const isActive = ref(false);
  const algorithm = ref<RoutingAlgorithm>("astar");
  const start = ref<number | null>(null);
  const end = ref<number | null>(null);
  const waypoints = ref<number[]>([]);

  const canCompute = computed(
    () => start.value !== null && end.value !== null,
  );

  async function activate(): Promise<void> {
    isActive.value = true;
    if (!store.routeGraph) {
      await store.loadRouteGraph();
    }
  }

  function deactivate(): void {
    isActive.value = false;
  }

  function clear(): void {
    start.value = null;
    end.value = null;
    waypoints.value = [];
    store.clearOptimalPath();
  }

  /**
   * Click-to-pick ordering: 1st click sets start, 2nd sets end, further
   * clicks append waypoints. Re-clicking a picked node removes it and
   * shifts the remaining picks down (end -> start, first waypoint -> end).
   */
  function toggleNode(nodeId: number): void {
    if (start.value === nodeId) {
      start.value = end.value;
      end.value = waypoints.value.shift() ?? null;
      return;
    }
    if (end.value === nodeId) {
      end.value = waypoints.value.shift() ?? null;
      return;
    }
    const waypointIndex = waypoints.value.indexOf(nodeId);
    if (waypointIndex !== -1) {
      waypoints.value.splice(waypointIndex, 1);
      return;
    }

    if (start.value === null) {
      start.value = nodeId;
    } else if (end.value === null) {
      end.value = nodeId;
    } else {
      waypoints.value.push(nodeId);
    }
  }

  async function compute(): Promise<void> {
    if (start.value === null || end.value === null) return;
    await store.computeOptimalPath({
      startNode: start.value,
      endNode: end.value,
      waypoints: waypoints.value,
      algorithm: algorithm.value,
    });
  }

  // A newly analyzed route invalidates any previously picked nodes.
  watch(
    () => store.analysis?.route_id,
    () => {
      deactivate();
      clear();
    },
  );

  return {
    isActive,
    algorithm,
    start,
    end,
    waypoints,
    canCompute,
    activate,
    deactivate,
    toggleNode,
    clear,
    compute,
  };
}
