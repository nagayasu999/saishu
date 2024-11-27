from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Node
from .forms import NodeForm
import heapq
import logging
from django.views.decorators.clickjacking import xframe_options_exempt
from decimal import Decimal

logger = logging.getLogger(__name__)

# 定数
DEFAULT_COEFFICIENT = Decimal('1.0')
BASIC_EDGE_COST = Decimal('1')

# Coefficientの更新と保持
def update_coefficient(request):
    try:
        if request.method == 'POST' and 'coefficient' in request.POST:
            coefficient = Decimal(request.POST.get('coefficient', DEFAULT_COEFFICIENT))
            request.session['coefficient'] = float(coefficient)
        else:
            coefficient = Decimal(request.session.get('coefficient', DEFAULT_COEFFICIENT))
        logger.debug(f"Coefficient updated or retrieved: {coefficient}")
    except ValueError:
        logger.error("Invalid coefficient value in update_coefficient.")
        coefficient = DEFAULT_COEFFICIENT
    return coefficient

# ノードの祖先チェック
def is_descendant(child, ancestor):
    logger.debug(f"Checking if Node {child.id} is a descendant of Node {ancestor.id}")
    current = child
    while current.parent:
        if current.parent.id == ancestor.id:
            return True
        current = current.parent
    return False

# ルートノードを取得
def get_root(node):
    while node.parent:
        node = node.parent
    return node

# ツリー内のノードを取得
def get_nodes_in_tree(node, nodes):
    root = get_root(node)
    return [n for n in nodes if get_root(n).id == root.id]

# ツリー内で最小のweightを持つノードを取得
def get_min_weight_node_in_tree(node, nodes):
    tree_nodes = get_nodes_in_tree(node, nodes)
    return min(tree_nodes, key=lambda x: x.weight)

# 全てのルートノードを取得
def build_graph(nodes, coefficient):
    graph = {node.id: [] for node in nodes}

    # ツリーごとにノードをグループ化し、最小weightのノードを特定
    trees = {}
    for node in nodes:
        root = get_root(node)
        if root.id not in trees:
            trees[root.id] = {
                'root': root,
                'nodes': [],
                'min_weight_nodes': []  # 最小weightのノードをリストで保持
            }
        trees[root.id]['nodes'].append(node)

    # 各ツリー内の最小weightを特定し、最小weightのノードをリストに追加
    for tree in trees.values():
        min_weight = min(n.weight for n in tree['nodes'])
        tree['min_weight_nodes'] = [n for n in tree['nodes'] if n.weight == min_weight]

    # 同一ツリー内のエッジを追加（要件5）
    for tree in trees.values():
        for node in tree['nodes']:
            # 親子関係のエッジ（要件5.H）
            if node.parent:
                weight_diff = node.parent.weight - node.weight
                if weight_diff < 0:
                    edge_cost = BASIC_EDGE_COST  # 要件6.L
                else:
                    edge_cost = round(weight_diff + 1, 1)  # 要件6.M
                graph[node.id].append((node.parent.id, edge_cost))
                graph[node.parent.id].append((node.id, edge_cost))

            # 同一階層のエッジ（要件5.I）
            siblings = [n for n in tree['nodes'] if n.parent_id == node.parent_id and n.id != node.id]
            for sibling in siblings:
                edge_cost = BASIC_EDGE_COST  # 基本エッジコスト（要件6.N）
                graph[node.id].append((sibling.id, edge_cost))

            # 最小weightのノードへのエッジを追加（最小weightが自分自身でない場合）
            for min_node in tree['min_weight_nodes']:
                if node.id != min_node.id:
                    weight_diff = min_node.weight - node.weight
                    if weight_diff < 0:
                        edge_cost = BASIC_EDGE_COST  # 要件6.L
                    else:
                        edge_cost = round(weight_diff + 1, 1)  # 要件6.M
                    # 既にエッジが存在しない場合のみ追加
                    if min_node.id not in [neighbor for neighbor, _ in graph[node.id]]:
                        graph[node.id].append((min_node.id, edge_cost))

    # 異なるツリー間のエッジを追加（要件4）
    for tree1_id, tree1 in trees.items():
        for tree2_id, tree2 in trees.items():
            if tree1_id == tree2_id:
                continue
            for node1 in tree1['nodes']:
                # 相手ツリー内で自分より軽いノードを探す
                lighter_nodes_in_other_tree = [n for n in tree2['nodes'] if n.weight < node1.weight]

                if lighter_nodes_in_other_tree:
                    # 自分より軽いノードへのエッジを追加（要件4.E）
                    for node2 in lighter_nodes_in_other_tree:
                        weight_diff = node2.weight - node1.weight
                        if weight_diff < 0:
                            edge_cost = BASIC_EDGE_COST  # 要件6.L
                        else:
                            edge_cost = round(weight_diff + 1, 1)  # 要件6.M
                        edge_cost *= coefficient  # 係数を適用（要件6.O）
                        graph[node1.id].append((node2.id, edge_cost))
                else:
                    # 相手ツリー内の最軽量ノードへのエッジを追加（要件4.F）
                    min_nodes_in_other_tree = tree2['min_weight_nodes']
                    for min_node_in_other_tree in min_nodes_in_other_tree:
                        weight_diff = min_node_in_other_tree.weight - node1.weight
                        if weight_diff < 0:
                            edge_cost = BASIC_EDGE_COST  # 要件6.L
                        else:
                            edge_cost = round(weight_diff + 1, 1)  # 要件6.M
                        edge_cost *= coefficient  # 係数を適用（要件6.O）
                        graph[node1.id].append((min_node_in_other_tree.id, edge_cost))

    return graph


# ノード間の通信コスト計算
def calculate_individual_communication_cost(nodes, coefficient=DEFAULT_COEFFICIENT):
    graph = build_graph(nodes, coefficient)

    # 各ノードからの最短経路コスト計算
    individual_costs = {}
    for start_node in nodes:
        costs = {node.id: Decimal('inf') for node in nodes}
        costs[start_node.id] = Decimal('0')
        priority_queue = [(Decimal('0'), start_node.id)]

        while priority_queue:
            current_cost, current_node_id = heapq.heappop(priority_queue)
            if current_cost > costs[current_node_id]:
                continue
            for neighbor_id, weight in graph[current_node_id]:
                new_cost = current_cost + weight
                if new_cost < costs[neighbor_id]:
                    costs[neighbor_id] = new_cost
                    heapq.heappush(priority_queue, (new_cost, neighbor_id))

        total_cost = sum(cost for cost in costs.values() if cost < Decimal('inf'))
        individual_costs[start_node.id] = round(float(total_cost), 1)

    return individual_costs

# 詳細なコスト計算
def calculate_detailed_costs(nodes, coefficient=DEFAULT_COEFFICIENT):
    graph = build_graph(nodes, coefficient)

    detailed_costs = {}
    for start_node in nodes:
        costs = {node.id: Decimal('inf') for node in nodes}
        paths = {node.id: [] for node in nodes}
        costs[start_node.id] = Decimal('0')
        paths[start_node.id] = [start_node]

        priority_queue = [(Decimal('0'), start_node.id)]

        while priority_queue:
            current_cost, current_node_id = heapq.heappop(priority_queue)
            if current_cost > costs[current_node_id]:
                continue
            for neighbor_id, weight in graph[current_node_id]:
                new_cost = current_cost + weight
                if new_cost < costs[neighbor_id]:
                    costs[neighbor_id] = new_cost
                    paths[neighbor_id] = paths[current_node_id] + [next(node for node in nodes if node.id == neighbor_id)]
                    heapq.heappush(priority_queue, (new_cost, neighbor_id))

        breakdown = [
            {
                "target_node": next(node.title for node in nodes if node.id == target_node),
                "cost": float(costs[target_node]),
                "path": [node.title for node in paths[target_node]],
            }
            for target_node in costs if costs[target_node] < Decimal('inf') and target_node != start_node.id
        ]

        detailed_costs[start_node.id] = {
            "total_cost": round(float(sum(costs.values())), 1),
            "breakdown": breakdown,
        }

    return detailed_costs

# コミュニケーションコストの計算コンテキスト
def calculate_cost_context(nodes, coefficient):
    individual_costs = calculate_individual_communication_cost(nodes, coefficient)
    detailed_costs = calculate_detailed_costs(nodes, coefficient)
    total_cost = sum(individual_costs.values())
    logger.debug(f"Total communication cost: {total_cost}")
    return {
        'individual_costs': individual_costs,
        'detailed_costs': detailed_costs,
        'total_cost': total_cost,
        'coefficient': coefficient,
    }

# ノード管理ページ
def node_cost(request):
    form = NodeForm(request.POST or None)
    coefficient = update_coefficient(request)

    if request.method == 'POST':
        if 'delete_all_nodes' in request.POST:
            Node.objects.all().delete()
            logger.info("All nodes deleted.")
            return redirect('nodecost')

        if form.is_valid():
            parent_id = request.POST.get('parent')
            parent_node = Node.objects.filter(id=parent_id).first() if parent_id else None
            quantity = int(request.POST.get('quantity', 1))
            for _ in range(quantity):
                Node.objects.create(
                    title=form.cleaned_data['title'],
                    weight=form.cleaned_data['weight'],
                    parent=parent_node,
                )
            logger.info(f"{quantity} nodes created.")
            return redirect('nodecost')

    nodes = Node.objects.all().order_by('-weight')
    cost_context = calculate_cost_context(nodes, coefficient)
    return render(request, 'nodecost/nodecost.html', {
        'form': form,
        'nodes': nodes,
        **cost_context,
    })

# 組織構造管理ページ
@xframe_options_exempt
def manage_organization(request):
    coefficient = update_coefficient(request)
    nodes = Node.objects.all().order_by('-weight')
    cost_context = calculate_cost_context(nodes, coefficient)

    return render(request, 'nodecost/manage_organization.html', {
        'nodes': nodes,
        **cost_context,
    })

# ノード削除
def delete_node(request):
    if request.method == 'POST':
        try:
            node_id = request.POST.get('node_id')
            node = get_object_or_404(Node, id=node_id)
            node.delete()
            return JsonResponse({'status': 'success', 'message': 'Node deleted successfully.'})
        except Exception as e:
            logger.error(f"Error deleting node: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

# ノード編集
def edit_node(request):
    if request.method == 'POST':
        try:
            node_id = request.POST.get("node_id")
            title = request.POST.get("title")
            weight = request.POST.get("weight")
            parent_id = request.POST.get("parent")

            node = get_object_or_404(Node, id=node_id)
            node.title = title
            node.weight = Decimal(weight)
            node.parent = Node.objects.filter(id=parent_id).first() if parent_id else None
            node.save()

            return JsonResponse({"status": "success", "message": "Node updated successfully."})
        except Exception as e:
            logger.error(f"Error editing node: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)

# コスト計算 (AJAX対応)
def calculate_costs(request):
    if request.method == 'POST':
        try:
            coefficient = update_coefficient(request)
            nodes = Node.objects.all()
            total_cost = sum(float(node.weight) * float(coefficient) for node in nodes)
            individual_costs = {
                node.id: round(float(node.weight) * float(coefficient), 2) for node in nodes
            }
            return JsonResponse({
                'status': 'success',
                'total_cost': round(total_cost, 2),
                'coefficient': float(coefficient),
                'individual_costs': individual_costs,
            })
        except Exception as e:
            logger.error(f"Error calculating costs: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
