# Terraform Driver Common Features (Variable Handling and Construction Code)

## Overview

Terraform is an infrastructure orchestration tool provided by HashiCorp. It generates an execution plan for infrastructure configuration coded in HCL (HashiCorp Configuration Language) and carries out the build. Terraform Cloud and Terraform Enterprise also support access policy management via Policy as Code.

As an ITA feature, the Terraform driver executes operations against Terraform and retrieves execution logs. Module files used for work execution (Plan/Apply) and Policy files used for PolicyCheck can be managed as modular, reusable parts within ITA. Variables within a Module can also be configured from the screen.

There are two types of Terraform driver:

- **Terraform Cloud/EP driver**: Creates Organizations/Workspaces on a Terraform Cloud/Enterprise instance registered in ITA, executes work (Plan/PolicyCheck/Apply), and retrieves work logs.
- **Terraform CLI driver**: Executes work (Plan/Apply) against Terraform installed in the same environment as ITA, and retrieves work logs.

## Variable Handling

With the Terraform driver, the concrete values of variables within a Module can be set from the ITA configuration screen. Anything defined in a variable block of the Module file is treated as a variable.

- **Normal variables**: Variables for which a concrete value is defined against the variable name. They are written according to the rules of the HCL variable block (`variable "xxx" { type = ○○  default = △△ }`); specifying `type` and `default` is not required.

Variables are extracted from Module materials uploaded to ITA, and their concrete values are registered by linking them with a parameter sheet. With the Terraform Cloud/EP driver, the "variable name" is registered as the Key and the "concrete value" as the Value in the linked Terraform Workspace's Variables management. With the Terraform CLI driver, they are written in the same way to the `terraform.tfvars` file generated at execution time.

### Variable Types

| type | Details | Member Variable Target | Assignment Order Target | Example `type` Notation | Example `default` Notation |
|---|---|---|---|---|---|
| string | String type | No | No | string | example |
| number | Number type | No | No | number | 123 |
| bool | Boolean type (true/false) | No | No | bool | true |
| list | Array type | No | Yes | list(string) | ["a","b","c"] |
| set | Array type (unique values; ITA does not perform uniqueness checks) | No | Yes | set(number) | [1,2,3] |
| tuple | Array type (the type at each index is fixed; shown as a dropdown selection in ITA) | Yes | No | tuple([string, number]) | ["abc", 2023] |
| map | Key-value type. Any type containing map must have HCL Setting turned ON in the auto value-assignment settings | No | No | map(string) | {"test_key"="test_value"} |
| object | Key-value type. Key names are treated as member variables (Japanese characters not allowed) | Yes | No | object({test_key=string}) | {"test_key"="test_value"} |
| any | Treated the same as string type in ITA | No | No | any | example |
| (not specified) | Treated the same as string type in ITA | No | No | - | example |

**Member variable target** (key names for key-value types): for object types, the KEY in `<KEY>=<TYPE>`; for tuple types, indices numbered from the start as `[0],[1],[2]...`. For items managed under Variable Nesting Management, indices are numbered as `[0],[1],[2]...` based on the maximum repeat count.

Example (object type `VAR_hoge { type = object({NAME=string, IP=string}) }`): registering `my_machine` for the member variable `NAME` and `192.168.100.1` for `IP` sends `{ NAME="my_machine" IP="192.168.100.1" }` to Terraform. For a tuple type (`type = tuple([string,number])`), registering `def` at `[0]` and `2024` at `[1]` sends `["def", 2024]`. For a nesting-managed type (`type = list(set(string))`), registering values at positions 1 and 2 of `[0]` and positions 1 and 2 of `[1]` sends something like `[["aaa","bbb"],["ccc","ddd"]]`.

**Assignment order target** (the order of assignment from the start when setting multiple concrete values): configurable when the variable, or the lowest-level variable in a nested structure, is of type list/set. For example, registering the values `abc` and `def` at assignment order 1 and 2 for a `list(string)` type sends `["abc","def"]`. For an `object({key=set(number)})` type, registering values `1` and `2` at order 1 and 2 for `key` sends `{key=[1,2]}`.

## How to Write Construction Code

- **Module**: Written in HCL (HashiCorp Configuration Language). See the official Terraform product manual for details.
- **Policy**: Written in Sentinel language (a feature available only with the Terraform Cloud/EP driver). See the official Terraform product manual for details.
